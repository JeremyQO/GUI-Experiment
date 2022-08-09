import scipy
from PyQt5 import uic
import time
import math
from functions.od import RedPitayaWebsocket
from scipy import optimize,spatial
from scipy.signal import find_peaks
# import vxi11 # https://github.com/python-ivi/python-vxi11
import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import matplotlib
from PID import PID
from PyQt5.QtCore import QThreadPool
from datetime import date, datetime
from widgets.worker import Worker
import matplotlib.pyplot as plt
from functions.stirap.calculate_Nat_stirap import NAtoms
_CONNECTION_ATTMPTS = 2

try:
    from functions.cavity_lock.cavity_lock import CavityLock
except:
    print("Run without calculate OD")
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')

from widgets.quantumWidget import QuantumWidget


class Cavity_lock_GUI(QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui

        super().__init__(ui, simulation)
        # up to here, nothing to change.

        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # Add outputs control UI
        self.outputsFrame=self.frame_4
        ui_outputs = os.path.join(os.path.dirname(__file__), "../scopeWidget/outputsControl.ui")
        uic.loadUi(ui_outputs, self.frame_4) # place outputs in frame 4

        self.connection_attempt = 0  # This holds connection attmeps. As long as this is < than _CONNECTION_ATTMPTS, will try to reconnect
        self.scope_parameters = {'new_parameters': False, 'OSC_TIME_SCALE': {'value':'1'}, 'OSC_CH1_SCALE': {'value':'1'},'OSC_CH1_SCALE': {'value':'1'}, 'OSC_DATA_SIZE':{'value':1024}}
        self.CHsUpdated = False
        self.listenForMouseClickCID = None
        self.rp = None  # Place holder
        self.pid = PID(1, 0,0,setpoint = 0, output_limits=(-10, 10))
        self.lockOn = False
        self.changedOutputs = False # this keeps track of changes done to outputs. if this is true, no total-redraw will happen (although usually we would update scope after any change in RP)
        self.signalLength = self.scope_parameters['OSC_DATA_SIZE']['value'] # 1024 by default

        # ---------- Rb Peaks ----------
        self.selectedPeaksXY = None
        self.indx_to_freq = [0]



        # ----------- Velocity Intrument -----------
        # try:
        #     self.velocity = vxi11.Instrument("169.254.46.36", 'gpib0,1')
        #     idn = self.velocity.ask("*IDN?")
        #     if idn != 'NewFocus 6312 GT3063 H0.39 C0.39':
        #         print('could not connect to velocity. Check connections.')
        #     self.print_to_dialogue(idn, color = 'green')
        #     self.velocityWavelength = float(self.velocity.ask('WAVE?'))
        #     self.doubleSpinBox_velocityWavelength.setValue(self.velocityWavelength)
        #     self.doubleSpinBox_velocityWavelength.valueChanged.connect(self.updateVelocityWavelength)
        # except:
        #     self.print_to_dialogue('Could not connect to velocity.', color= 'red')

        # -- connect --
        self.connectButtonsAndSpinboxes()
        self.update_plot_params()

        self.utils_connect_worker()


    def connectButtonsAndSpinboxes(self):
        self.pushButton_utils_Connect.clicked.connect(self.utils_connect_worker)
        self.pushButton_saveCurrentData.clicked.connect(self.saveCurrentDataClicked)
        self.pushButton_updatePlotDisplay.clicked.connect(self.updatePlotDisplay)
        self.outputsFrame.pushButton_StartLock.clicked.connect(self.toggleLock)
        self.outputsFrame.pushButton_selectPeak.clicked.connect(self.scopeListenForMouseClick)
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)
        self.checkBox_Rb_lines.clicked.connect(self.chns_update)
        self.checkBox_Cavity_transm.clicked.connect(self.chns_update)

        self.checkBox_CH1Inverse.clicked.connect(self.setInverseChns)
        self.checkBox_CH2Inverse.clicked.connect(self.setInverseChns)

        # PID spniboxes
        self.outputsFrame.doubleSpinBox_P.valueChanged.connect(self.updatePID)
        self.outputsFrame.doubleSpinBox_I.valueChanged.connect(self.updatePID)
        self.outputsFrame.doubleSpinBox_D.valueChanged.connect(self.updatePID)

        # Output spinboxes
        self.outputsFrame.comboBox_ch1OutFunction.currentIndexChanged.connect(self.updateOutputChannels)
        self.outputsFrame.comboBox_ch2OutFunction.currentIndexChanged.connect(self.updateOutputChannels)
        self.outputsFrame.doubleSpinBox_ch1OutAmp.valueChanged.connect(self.updateOutputChannels)
        self.outputsFrame.doubleSpinBox_ch2OutAmp.valueChanged.connect(self.updateOutputChannels)
        self.outputsFrame.doubleSpinBox_ch1OutFreq.valueChanged.connect(self.updateOutputChannels)
        self.outputsFrame.doubleSpinBox_ch2OutFreq.valueChanged.connect(self.updateOutputChannels)
        self.outputsFrame.doubleSpinBox_ch1OutOffset.valueChanged.connect(self.updateOutputChannels)
        self.outputsFrame.doubleSpinBox_ch2OutOffset.valueChanged.connect(self.updateOutputChannels)
        self.outputsFrame.checkBox_ch1OuputState.stateChanged.connect(self.updateOutputChannels)
        self.outputsFrame.checkBox_ch2OuputState.stateChanged.connect(self.updateOutputChannels)

    def updateVelocityWavelength(self):
        v = self.doubleSpinBox_velocityWavelength.value()
        self.velocity.write('WAVE {:.2f}'.format(v))
        res = self.velocity.ask('WAVE?')
        if res == 'Unknown Command':
            self.print_to_dialogue('Could not change Velocity wavelength', color = 'red')
            self.doubleSpinBox_velocityWavelength.setValue(self.velocityWavelength)
        else:
            self.velocityWavelength = v

    def setInverseChns(self):
        self.rp.set_inverseChannel(ch=1, value = self.checkBox_CH1Inverse.isChecked())
        self.rp.set_inverseChannel(ch=2, value = self.checkBox_CH2Inverse.isChecked())

    def update_plot_params(self):
        self.Avg_num_CH1 = int(self.spinBox_averaging_CH1.value())
        self.Avg_num_CH2 = int(self.spinBox_averaging_CH2.value())
        self.Rb_lines_Data = np.zeros((self.Avg_num_CH1, self.signalLength))  # Place holder
        self.Cavity_Transmission_Data = np.zeros((self.Avg_num_CH2, self.signalLength))  # Place holder
        self.avg_indx_CH1 = 0
        self.avg_indx_CH2 = 0

    def updateTriggerDelay(self):
        t = float(self.doubleSpinBox_triggerDelay.value())  # ms
        l = float(self.doubleSpinBox_triggerLevel.value()) # in mV
        s = self.comboBox_triggerSource.currentText() # text
        self.rp.set_triggerSource(s)
        self.rp.set_triggerDelay(t)
        self.rp.set_triggerLevel(l)
        self.print_to_dialogue("Trigger delay changed to %f ms; Source: %s; Level: %2.f [V]" % (t,s,l))

    def updateTimeScale(self):
        t = float(self.doubleSpinBox_timeScale.text())
        self.rp.set_timeScale(t)
        self.print_to_dialogue("Time scale changed to %f ms" % t)

    def updateAveraging(self):
        self.Avg_num_CH1 = int(self.spinBox_averaging_CH1.value())
        self.Avg_num_CH2 = int(self.spinBox_averaging_CH2.value())
        self.Rb_lines_Data = np.zeros((self.Avg_num_CH1, self.signalLength))  # Place holder
        self.Cavity_Transmission_Data = np.zeros((self.Avg_num_CH2, self.signalLength))  # Place holder
        self.avg_indx_CH1 = 0
        self.avg_indx_CH2 = 0
        self.print_to_dialogue("Data averaging on CH1 changed to %i \n" %self.Avg_num_CH1 + "Data averaging on CH2 changed to %i \n" %self.Avg_num_CH2)

    def updatePlotDisplay(self):
        self.updateTriggerDelay()
        self.updateTimeScale()
        self.updateAveraging()

    def updatePID(self):
        P, I, D = float(self.outputsFrame.doubleSpinBox_P.value()), float(self.outputsFrame.doubleSpinBox_I.value()), float(self.outputsFrame.doubleSpinBox_D.value())
        self.pid.tunings = (P, I, D)

    def toggleLock(self):
        self.lockOn = not self.lockOn
        self.outputsFrame.checkBox_ch1OuputState.setCheckState(self.lockOn)

    def updateOutputChannels(self):
        # TODO: add hold-update to rp
        self.changedOutputs = True
        self.rp.set_outputFunction(output=1, function=str(self.outputsFrame.comboBox_ch1OutFunction.currentText()))
        self.rp.set_outputFunction(output=2, function=str(self.outputsFrame.comboBox_ch2OutFunction.currentText()))
        self.rp.set_outputAmplitude(output=1, v=float(self.outputsFrame.doubleSpinBox_ch1OutAmp.value()))
        self.rp.set_outputAmplitude(output=2, v=float(self.outputsFrame.doubleSpinBox_ch2OutAmp.value()))
        self.rp.set_outputFrequency(output=1, freq=float(self.outputsFrame.doubleSpinBox_ch1OutFreq.value()))
        self.rp.set_outputFrequency(output=2, freq=float(self.outputsFrame.doubleSpinBox_ch2OutFreq.value()))
        self.rp.set_outputOffset(output=1, v=float(self.outputsFrame.doubleSpinBox_ch1OutOffset.value()))
        self.rp.set_outputOffset(output=2, v=float(self.outputsFrame.doubleSpinBox_ch2OutOffset.value()))
        self.rp.set_outputState(output=1, state=bool(self.outputsFrame.checkBox_ch1OuputState.checkState()))
        self.rp.set_outputState(output=2, state=bool(self.outputsFrame.checkBox_ch2OuputState.checkState()))
        self.rp.updateParameters()

    def chns_update(self):
        self.scope_parameters['new_parameters'] = True

    def enable_interface(self, v): #TODO ?????
        self.frame_4.setEnabled(v)
        self.frame_parameters.setEnabled(v)

    def utils_connect_worker(self):
        worker = Worker(self.utils_connect)
        self.pushButton_utils_Connect.setDisabled(True)
        worker.signals.finished.connect(self.utils_connect_finished)
        self.threadpool.start(worker)

    def utils_connect_finished(self):
        self.enable_interface(True)
        self.pushButton_utils_Connect.setEnabled(True)


    def utils_connect(self, progress_callback):
        self.print_to_dialogue("Connecting to RedPitayas...")
        time.sleep(0.1)
        # self.connectOPX()
        # ---- Connect Red-Pitaya ------
        RPworker = Worker(self.redPitayaConnect) #Trying to work on a different thread...
        self.threadpool.start(RPworker)

    def saveCurrentDataClicked(self):
        timeScale = np.linspace(0, float(self.scope_parameters['OSC_TIME_SCALE']['value']) * 10, num=int(self.scope_parameters['OSC_DATA_SIZE']['value']))
        now = datetime.now()
        today = date.today()
        datadir = os.path.join("C:\\", "Pycharm", "Expriements", "DATA", "CavityLock")
        todayformated = today.strftime("%B-%d-%Y")
        todaydatadir = os.path.join(datadir, todayformated)
        nowformated = now.strftime("%Hh%Mm%Ss")
        try:
            os.makedirs(todaydatadir)
            self.print_to_dialogue("Created folder DATA/CavityLock/%s" % (todayformated))
            self.print_to_dialogue("Data Saved")
        except FileExistsError:
            self.print_to_dialogue("Data Saved")

        self.datafile = os.path.join(todaydatadir, nowformated + ".txt")
        meta = "Traces from the RedPitaya, obtained on %s at %s.\n" % (todayformated, nowformated)
        # np.savez_compressed(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data, CH2=self.Cavity_Transmission_Data, time=timeScale, meta=meta)
        np.save(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data,CH2=self.Cavity_Transmission_Data, time=timeScale, meta=meta)


    def redPitayaConnect(self, progress_callback):
        RpHost = ["rp-ffffb4.local","rp-f08c22.local", "rp-f08c36.local"]
        self.rp = RedPitayaWebsocket.Redpitaya(host="rp-ffffb4.local", got_data_callback=self.update_scope,dialogue_print_callback=self.print_to_dialogue)

        if self.rp.connected:
            self.connection_attempt = 0 # connection
            self.print_to_dialogue("RedPitayas are connected.", color = 'green')
            self.rp.run()
        else:
            self.print_to_dialogue("Unable to connect to RedPitaya.", color= 'red')
            self.rp.close()
            self.rp = None
            if self.connection_attempt < _CONNECTION_ATTMPTS:
                self.print_to_dialogue('Trying to reconnect... (attempt = %d out of %d)' % (self.connection_attempt + 1, _CONNECTION_ATTMPTS))
                self.connection_attempt = self.connection_attempt + 1
                self.redPitayaConnect(progress_callback)

    def scopeListenForMouseClick(self):
        def mouseClickOnScope(event): # what should do on mouse click, when listening
            # Find nearest peak
            if self.selectedPeaksXY is None : # id first click, create list of peaks...
                self.selectedPeaksXY = [np.array([event.xdata,event.ydata])]
                self.print_to_dialogue('Select second peak on scope...', color='green')
            else: #if second peak, append it.
                self.selectedPeaksXY.append(np.array([event.xdata,event.ydata]))
            if len(self.selectedPeaksXY) >= 2:
                # If clicked on canvas, and already has two peaks selected, stop listening for click
                self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseClickCID)
                self.listenForMouseClickCID = None

        if self.listenForMouseClickCID is None:  # start listening
            self.listenForMouseClickCID = self.widgetPlot.canvas.mpl_connect('button_press_event', mouseClickOnScope)
            self.selectedPeaksXY = None
            self.print_to_dialogue('Select first peak on scope...', color = 'green')
        else: # stop listen
            self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseClickCID)
            self.listenForMouseClickCID = None

    def updateSelectedPeak(self, peaksLocation):
        # Run over all current selected peaks; Assume the 1st selected peak belongs to 1st channel etc.
        # Find the closest peak to the selected one in the relevant channel; update.
        for i, curSelectedPeak in enumerate(self.selectedPeaksXY):
            nearestPeakIndex = spatial.KDTree(peaksLocation[i]).query(curSelectedPeak)[1]  # [0] would have given us distance
            nearestPeakLocation = peaksLocation[i][nearestPeakIndex]
            self.selectedPeaksXY[i] = np.array(nearestPeakLocation)  # update location of selected peak to BE the nearest peak

    # Never call this method. this is called by RedPitaya
    def update_scope(self, data, parameters):
        if self.rp.firstRun:
            # Set default from display...
            self.comboBox_triggerSource.setCurrentIndex(2) # Select EXT trigger...
            self.updatePlotDisplay()
            self.setInverseChns()
            self.showHideParametersWindow()
            self.chns_update()
            self.updateOutputChannels()
            self.rp.firstRun = False

        # ---------------- Handle Redraws and data reading ----------------
        # This is true only when some parameters were changed on RP, prompting a total redraw of the plot (in other cases, updating the data suffices)
        redraw = (parameters['new_parameters'] or self.CHsUpdated) and not self.changedOutputs  # if last change was to outputs, dont bother to redraw all
        if redraw:
            self.scope_parameters = parameters  # keep all the parameters. we need them.
            self.CHsUpdated = False

        RB_LINES_JUMP_THRESHOLD = 0.1  # threshold in volts for throwing rb lines data if jump occurs

        # gauss7 = np.array([0.0702, 0.1311, 0.1907, 0.2161, 0.1907, 0.1311, 0.0702])
        # Rb_lines_Data_with_conv = np.convolve(np.array(data[0]), gauss7, 'same')
        # Squared_Rb_lines_Data = [x ** 2 for x in Rb_lines_Data_with_conv]
        Squared_Rb_lines_Data = [x ** 2 for x in data[0]]

        # Squared_Rb_lines_Data = [x ** 2 for x in data[0]]
        if (sum(Squared_Rb_lines_Data) < RB_LINES_JUMP_THRESHOLD) & (len([x for x in np.absolute(data[0]) if x > 0.01]) > 2): #throws data when jump in channel occurs (due to turn off of the laser)
            # print(max(np.absolute(data[0])))
            print(sum(Squared_Rb_lines_Data))
            self.Rb_lines_Data[self.avg_indx_CH1] = Squared_Rb_lines_Data  # Insert new data
            self.avg_indx_CH1 = (self.avg_indx_CH1 + 1) % self.Avg_num_CH1
        # if (max(-np.array(data[1])) > 0.01) & (sum(np.array(data[1])) > -7):
        # print(sum(np.array(data[1])))
        self.Cavity_Transmission_Data[self.avg_indx_CH2] = data[1]  # Insert new data
        self.avg_indx_CH2 = (self.avg_indx_CH2 + 1) % self.Avg_num_CH2
        self.changedOutputs = False

        # ---------------- Average data  ----------------
        # Calculate avarage data and find peaks position (indx) and properties:
        Avg_data = []
        if self.checkBox_Rb_lines.isChecked():
            self.Rb_lines_Avg_Data = np.sqrt(np.average(self.Rb_lines_Data, axis=0))
            # print(self.Rb_lines_Avg_Data)
            Avg_data = Avg_data + [self.Rb_lines_Avg_Data]
        if self.checkBox_Cavity_transm.isChecked():
            self.Cavity_Transmission_Avg_Data = np.average(self.Cavity_Transmission_Data, axis=0)
            Avg_data = Avg_data + [self.Cavity_Transmission_Avg_Data]

        # ---------------- Handle Rb Peaks ----------------
        Rb_peaks, Cavity_peak, Rb_properties, Cavity_properties = [], [], {}, {} # by default, none
        if self.checkBox_Rb_lines.isChecked():
            Rb_peaks, Rb_properties = find_peaks(self.Rb_lines_Avg_Data,
                                                 distance=float(self.spinBox_distance_ch1.value()),
                                                 prominence=float(self.doubleSpinBox_prominence_ch1.value()),
                                                 width=float(self.spinBox_width_ch1.value()))
        if self.checkBox_Cavity_transm.isChecked():
            Cavity_peak, Cavity_properties = find_peaks(-self.Cavity_Transmission_Avg_Data,
                                                        distance=float(self.spinBox_distance_ch2.value()),
                                                        prominence=float(self.doubleSpinBox_prominence_ch2.value()),
                                                        width=float(self.spinBox_width_ch2.value()))

        # ------- Scales -------
        # At this point we assume we have a corrcet calibration polynomial in @self.index_to_freq
        # Set Values for x-axis frequency:
        time_scale = float(self.scope_parameters['OSC_TIME_SCALE']['value'])
        indx_to_time = float(10 * time_scale / self.scope_parameters['OSC_DATA_SIZE']['value'])
        # time-scale
        x_axis = np.linspace(0, time_scale * 10, num=int(self.scope_parameters['OSC_DATA_SIZE']['value']))
        x_ticks = np.arange(x_axis[0], x_axis[-1], time_scale)

        # Secondary axis
        indx_to_freq = self.indx_to_freq[0]
        def timeToFreqScale(t):
            print(indx_to_freq)
            return (t - Rb_peaks[0]) * indx_to_freq
        def freqToTimeScale(f):
            print(indx_to_freq)

            return f / indx_to_freq + Rb_peaks[0]


        y_scale = float(self.doubleSpinBox_VtoDiv.text())
        y_offset = float(self.doubleSpinBox_VOffset.text())
        y_ticks = np.arange(y_offset - y_scale * 5, y_offset + y_scale * 5, y_scale)

        # --------- select peak -----------
        # At this point we have the location of the selected peak, either by (1) recent mouse click or (2) the last known location of the peak
        if self.selectedPeaksXY is not None and type(self.selectedPeaksXY) == list:# and len(self.selectedPeaksXY) == 2 and type(self.selectedPeaksXY[0]) == np.ndarray and type(self.selectedPeaksXY[1]) == np.ndarray:
            chn1_peaksLocation = np.array([[x_axis[p], Avg_data[0][p]] for p in Rb_peaks])  # all the peaks as coordinates
            chn2_peaksLocation = np.array([[x_axis[p], Avg_data[1][p]] for p in Cavity_peak])  # all the peaks as coordinates
            self.updateSelectedPeak([chn1_peaksLocation, chn2_peaksLocation])

        # ----------- text box -----------
        # to be printed in lower right corner
        text_box_string = None

        if self.outputsFrame.checkBox_fitLorentzian.isChecked():
            popt = self.fitMultipleLorentzians(xData=x_axis, yData=Avg_data[1], peaks_indices=Rb_peaks,
                                        peaks_init_width=(Rb_properties['widths'] * indx_to_time))  # just an attempt. this runs very slowly.
            # popt2 = self.fitMultipleLorentzians(xData=x_axis, yData=Avg_data[1], peaks_indices=Cavity_peak,
            #                             peaks_init_width=(Rb_properties['widths'] * indx_to_time))  # just an attempt. this runs very slowly.
            params_text = self.multipleLorentziansParamsToText(popt)
            text_box_string = 'Calibration: \n' + str(self.indx_to_freq) +'\n'
            text_box_string += 'Found %d Lorentzians: \n'%len(Rb_peaks) + params_text

        # --------- plot ---------
        # Prepare data for display:
        labels = ["CH1 - Vortex Rb lines", "CH2 - Cavity transmission"]
        self.widgetPlot.plot_Scope(x_axis, Avg_data, autoscale=self.checkBox_plotAutoscale.isChecked(), redraw=redraw, labels = labels, x_ticks = x_ticks, y_ticks= y_ticks,
                                   aux_plotting_func = self.widgetPlot.plot_Scatter, scatter_y_data = np.concatenate([Avg_data[0][Rb_peaks], Avg_data[1][Cavity_peak]]),
                                   scatter_x_data = np.concatenate([x_axis[Rb_peaks], x_axis[Cavity_peak]]),mark_peak = self.selectedPeaksXY, text_box = text_box_string)

        # --------- Lock -----------
        if self.lockOn and self.selectedPeaksXY and len(self.selectedPeaksXY) == 2: # if, and only if, we have selected two peaks to lock on
           self.lockPeakToPeak()

        # -------- Save Data  --------:
        if self.checkBox_saveData.isChecked():
            self.saveCurrentDataClicked()

    def lockPeakToPeak(self):
        errorDirection = 1 if self.outputsFrame.checkBox_lockInverse.isChecked() else - 1
        errorSignal = (self.selectedPeaksXY[1][0] - self.selectedPeaksXY[0][0]) * (errorDirection)
        output = self.pid(errorSignal)
        print('Error Signal: ', errorSignal, 'Output: ', output)
        # ------- set output --------------
        # It's a problem with Red-Pitaya: to get 10V DC output, one has to set both Amp and Offset to 5V
        self.outputsFrame.doubleSpinBox_ch1OutAmp.setValue(float(output) / 2)
        self.outputsFrame.doubleSpinBox_ch1OutOffset.setValue(float(output) / 2)

if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Cavity_lock_GUI(simulation=simulation)
    window.show()
    app.exec_()
    sys.exit(app.exec_())