
from PyQt5 import uic
import time
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

        self.connection_attempt = 0  # This holds connection attmeps. As long as this is < than _CONNECTION_ATTMPTS, will try to reconnect
        self.scope_parameters = {'new_parameters': False, 'OSC_TIME_SCALE': {'value':'1'}, 'OSC_CH1_SCALE': {'value':'1'},'OSC_CH1_SCALE': {'value':'1'}, 'OSC_DATA_SIZE':{'value':1024}}
        self.CHsUpdated = False
        self.listenForMouseClickCID = None
        self.rp = None  # Place holder
        self.pid = PID(1, 0,0,setpoint = 0)
        self.lockOn = False
        self.changedOutputs = False # this keeps track of changes done to outputs. if this is true, no total-redraw will happen (although usually we would update scope after any change in RP)
        self.signalLength = self.scope_parameters['OSC_DATA_SIZE']['value'] # 1024 by default

        # ---------- Rb Peaks ----------
        self.Rb_peaks_default_value = [172, 259, 346, 409, 496, 646]
        self.Rb_peak_freq = [0, 36.1, 72.2, 114.6, 150.7, 229]
        self.peaks_tags = ['1-0', '1-0/1', '1-1', '1-0/2', '1-1/2', '1-2']
        self.selectedPeaksXY = None
        self.calibrateRbPeaks = False # should calibrate peaks according to next data batch that arrives? calibration will be printed and saved in self.index_to_freq
        self.indx_to_freq = [0]

        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        # ui_stirap_sequence = os.path.join(os.path.dirname(__file__), "STIRAP_sequence.ui")  # if ui is None else ui
        super().__init__(ui, simulation)
        # up to here, nothing to change.
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # self.widgetPlot.plot([None], [None])
        # self.rp = scpi.Redpitaya("rp-f08c22.local", trigger_delay=28e6, decimation=64)
        self.pushButton_utils_Connect.clicked.connect(self.utils_connect_worker)
        # self.pushButton_utils_Connect.clicked.connect(self.redPitayaConnect)
        self.pushButton_saveCurrentData.clicked.connect(self.saveCurrentDataClicked)
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)
        self.checkBox_Rb_lines.clicked.connect(self.chns_update)
        self.checkBox_Cavity_transm.clicked.connect(self.chns_update)
        # self.checkBox_Rb_lines.clicked.connect(self.acquire_traces_worker)
        self.pushButton_updatePlotDisplay.clicked.connect(self.updatePlotDisplay)
        self.pushButton_StartLock.clicked.connect(self.toggleLock)
        self.pushButton_selectPeak.clicked.connect(self.scopeListenForMouseClick)
        self.pushButton_calibratePeaks.clicked.connect(self.calibratePeaks)
        self.checkBox_FreqScale.clicked.connect(self.chns_update)
        self.checkBox_F1.clicked.connect(self.Rb_peak_freq_F1_update)
        self.checkBox_F2.clicked.connect(self.Rb_peak_freq_F2_update)
        self.checkBox_CH1Inverse.clicked.connect(self.setInverseChns)
        self.checkBox_CH2Inverse.clicked.connect(self.setInverseChns)
        self.update_plot_params()

        self.connectSpinboxes()

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
        self.utils_connect_worker()


    def connectSpinboxes(self):
        # PID spniboxes
        self.doubleSpinBox_P.valueChanged.connect(self.updatePID)
        self.doubleSpinBox_I.valueChanged.connect(self.updatePID)
        self.doubleSpinBox_D.valueChanged.connect(self.updatePID)

        # Output spinboxes
        self.comboBox_ch1OutFunction.currentIndexChanged.connect(self.updateOutputChannels)
        self.comboBox_ch2OutFunction.currentIndexChanged.connect(self.updateOutputChannels)
        self.doubleSpinBox_ch1OutAmp.valueChanged.connect(self.updateOutputChannels)
        self.doubleSpinBox_ch2OutAmp.valueChanged.connect(self.updateOutputChannels)
        self.doubleSpinBox_ch1OutFreq.valueChanged.connect(self.updateOutputChannels)
        self.doubleSpinBox_ch2OutFreq.valueChanged.connect(self.updateOutputChannels)
        self.doubleSpinBox_ch1OutOffset.valueChanged.connect(self.updateOutputChannels)
        self.doubleSpinBox_ch2OutOffset.valueChanged.connect(self.updateOutputChannels)
        self.checkBox_ch1OuputState.stateChanged.connect(self.updateOutputChannels)
        self.checkBox_ch2OuputState.stateChanged.connect(self.updateOutputChannels)
    def updateVelocityWavelength(self):
        v = self.doubleSpinBox_velocityWavelength.value()
        self.velocity.write('WAVE {:.2f}'.format(v))
        res = self.velocity.ask('WAVE?')
        if res == 'Unknown Command':
            self.print_to_dialogue('Could not change Velocity wavelength', color = 'red')
            self.doubleSpinBox_velocityWavelength.setValue(self.velocityWavelength)
        else:
            self.velocityWavelength = v

    def Rb_peak_freq_F1_update(self):
        if self.checkBox_F1.isChecked():
            self.Rb_peak_freq = [0, 36.1, 72.2, 114.6, 150.7, 229]
            self.peaks_tags = ['1-0', '1-0/1', '1-1', '1-0/2', '1-1/2', '1-2']
            self.checkBox_F2.setChecked(False)
            self.chns_update()

    def Rb_peak_freq_F2_update(self):
        if self.checkBox_F2.isChecked():
            self.Rb_peak_freq = [0, 78.47, 156.95, 211.8, 290.27, 423.6]
            self.peaks_tags = ['2-1', '2-1/2', '2-2', '2-1/3', '2-2/3', '2-3']
            self.checkBox_F1.setChecked(False)
            self.chns_update()

    def setInverseChns(self):
        self.rp.set_inverseChannel(ch=1, value = self.checkBox_CH1Inverse.isChecked())
        self.rp.set_inverseChannel(ch=2, value =  self.checkBox_CH2Inverse.isChecked())

    def update_plot_params(self):
        self.Avg_num = int(self.spinBox_averaging.value())
        self.Rb_lines_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.Cavity_Transmission_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.avg_indx = 0

    def updateDecimation(self):
        dec = Decimation_options[self.comboBox_TimeScale.currentIndex()]
        # self.rp.set_decimation(dec)
        # self.lineEdit_triggerDelay.setText(str(int(self.rp.triggerDelay)*1e-3))
        self.print_to_dialogue("Decimation changed to %i" % dec)

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
        self.Avg_num = int(self.spinBox_averaging.value())
        self.Rb_lines_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.Cavity_Transmission_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.avg_indx = 0
        self.print_to_dialogue("Data averaging changed to %i" % self.Avg_num)

    def calibratePeaks(self):
        self.checkBox_liveCalibratePeaks.setChecked(True) # make sure this is checked (true)
        self.calibrateRbPeaks = True

    def updatePlotDisplay(self):
        self.updateTriggerDelay()
        self.updateTimeScale()
        self.updateAveraging()

    def updatePID(self):
        P, I, D = float(self.doubleSpinBox_P.value()), float(self.doubleSpinBox_I.value()), float(self.doubleSpinBox_D.value())
        self.pid.tunings = (P, I, D)
    def toggleLock(self):
        self.lockOn = not self.lockOn
        self.checkBox_ch1OuputState.setCheckState(self.lockOn)

    def updateOutputChannels(self):
        self.changedOutputs = True
        self.rp.set_outputFunction(output=1, function=str(self.comboBox_ch1OutFunction.currentText()))
        self.rp.set_outputFunction(output=2, function=str(self.comboBox_ch2OutFunction.currentText()))
        self.rp.set_outputAmplitude(output=1, v=float(self.doubleSpinBox_ch1OutAmp.value()))
        self.rp.set_outputAmplitude(output=2, v=float(self.doubleSpinBox_ch2OutAmp.value()))
        self.rp.set_outputFrequency(output=1, freq=float(self.doubleSpinBox_ch1OutFreq.value()))
        self.rp.set_outputFrequency(output=2, freq=float(self.doubleSpinBox_ch2OutFreq.value()))
        self.rp.set_outputOffset(output=1, v=float(self.doubleSpinBox_ch1OutOffset.value()))
        self.rp.set_outputOffset(output=2, v=float(self.doubleSpinBox_ch2OutOffset.value()))
        self.rp.set_outputState(output=1, state=bool(self.checkBox_ch1OuputState.checkState()))
        self.rp.set_outputState(output=2, state=bool(self.checkBox_ch2OuputState.checkState()))
        self.rp.updateParameters()

    def chns_update(self):
        self.scope_parameters['new_parameters'] = True
        # self.CHsUpdated = True

    def enable_interface(self, v):
        self.frame_4.setEnabled(v)
        self.frame_parameters.setEnabled(v)

    def utils_connect_worker(self):
        worker = Worker(self.utils_connect)
        self.pushButton_utils_Connect.setDisabled(True)
        worker.signals.finished.connect(self.utils_connect_finished)
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def utils_connect_finished(self):
        self.enable_interface(True)
        self.pushButton_utils_Connect.setEnabled(True)



    def utils_connect(self, progress_callback):
        self.print_to_dialogue("Connecting to RedPitayas...")
        time.sleep(0.1)
        # self.connectOPX()
        # self.updateDecimation()
        # self.updateTriggerDelay()
        self.display_traces_worker()

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
        np.save(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data,
                            CH2=self.Cavity_Transmission_Data, time=timeScale, meta=meta)
    def display_traces_worker(self):
        #worker = Worker(self.display_traces_loop)
        worker = Worker(self.redPitayaConnect) #Trying to work on a different thread...
        self.threadpool.start(worker)

    def redPitayaConnect(self, progress_callback):
        self.rp = RedPitayaWebsocket.Redpitaya(host="rp-ffffb4.local", got_data_callback=self.update_scope,
                                               dialogue_print_callback=self.print_to_dialogue)
        # self.rp = RedPitayaWebsocket.Redpitaya(host="rp-f08c22.local", got_data_callback=self.update_scope, dialogue_print_callback = self.print_to_dialogue)
        # self.rp = RedPitayaWebsocket.Redpitaya(host="rp-f08c36.local", got_data_callback=self.update_scope, dialogue_print_callback=self.print_to_dialogue)
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
        for i, pkLocation in enumerate(peaksLocation):
            nearestPeakIndex = spatial.KDTree(pkLocation).query(self.selectedPeaksXY[i])[1]  # [0] would have given us distance
            nearestPeakLocation = pkLocation[nearestPeakIndex]
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
            # self.selectedPeaksXY = None  # if it was necessary to redraw everything, peak will probably be lost
        self.Rb_lines_Data[self.avg_indx] = data[0]  # Insert new data
        self.Cavity_Transmission_Data[self.avg_indx] = data[1]  # Insert new data
        self.avg_indx = (self.avg_indx + 1) % self.Avg_num
        self.changedOutputs = False
        # ---------------- Average data  ----------------
        # Calculate avarage data and find peaks position (indx) and properties:
        Avg_data = []
        if self.checkBox_Rb_lines.isChecked():
            self.Rb_lines_Avg_Data = np.average(self.Rb_lines_Data, axis=0)
            Avg_data = Avg_data + [self.Rb_lines_Avg_Data]
        if self.checkBox_Cavity_transm.isChecked():
            self.Cavity_Transmission_Avg_Data = np.average(self.Cavity_Transmission_Data, axis=0)
            Avg_data = Avg_data + [self.Cavity_Transmission_Avg_Data]

        # ---------------- Handle Rb Peaks ----------------
        Rb_peaks,Cavity_peak, Rb_properties, Cavity_properties = [], [],{},{} # by default, none
        if self.checkBox_Rb_lines.isChecked():
            Rb_peaks, Rb_properties = find_peaks(self.Rb_lines_Avg_Data,
                                                 distance=float(self.spinBox_distance_ch1.value()),
                                                 prominence=float(self.doubleSpinBox_prominence_ch1.value()),
                                                 width=float(self.spinBox_width_ch1.value()))
        if self.checkBox_Cavity_transm.isChecked():
            Cavity_peak, Cavity_properties = find_peaks(self.Cavity_Transmission_Avg_Data,
                                                        distance=float(self.spinBox_distance_ch2.value()),
                                                        prominence=float(self.doubleSpinBox_prominence_ch2.value()),
                                                        width=float(self.spinBox_width_ch2.value()))
        # Rescale index to frequency detuning[MHz] from transition F=1->F'=0:
        # First - see if 6 peaks are found
        self.pushButton_calibratePeaks.setEnabled(len(Rb_peaks) == len(self.Rb_peak_freq)) # Check we have enough peaks to preform calibration.
        if len(Rb_peaks) == len(self.Rb_peak_freq): # if we do have enough peaks to preform calibration then:
            self.Rb_peaks_default_value = Rb_peaks # update peaks default location (necessary...?) prbly not
            # -------------- Rb calibration, index to Frequency ---------------
            # print(['%3.1f' %i for i in self.indx_to_freq * Rb_peaks-100.0])
            if self.checkBox_liveCalibratePeaks.isChecked():
                self.indx_to_freq = np.poly1d(np.polyfit(Rb_peaks, self.Rb_peak_freq, 1))
                if self.calibrateRbPeaks:
                    self.calibrateRbPeaks = False  # only need to calibrate once.
                    self.checkBox_liveCalibratePeaks.setChecked(False)  # uncheck box.
                    self.printPeaksInformation()
        # else:
        #     Rb_peaks = self.Rb_peaks_default_value  # if not - use previous values


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

        secondary_x_axis_func = None
        if self.checkBox_FreqScale.isChecked():  # if should add secondary axis
            secondary_x_axis_func = (timeToFreqScale, freqToTimeScale)


        y_scale = float(self.doubleSpinBox_VtoDiv.text())
        y_offset = float(self.doubleSpinBox_VOffset.text())
        y_ticks = np.arange(y_offset - y_scale * 5, y_offset + y_scale * 5, y_scale)

        # --------- select peak -----------
        # At this point we have the location of the selected peak, either by (1) recent mouse click or (2) the last known location of the peak
        if self.selectedPeaksXY is not None and type(self.selectedPeaksXY) == list and len(self.selectedPeaksXY) == 2 and type(self.selectedPeaksXY[0]) == np.ndarray and type(self.selectedPeaksXY[1]) == np.ndarray:
            chn1_peaksLocation = np.array([[x_axis[p], Avg_data[0][p]] for p in Rb_peaks])  # all the peaks as coordinates
            chn2_peaksLocation = np.array([[x_axis[p], Avg_data[1][p]] for p in Cavity_peak])  # all the peaks as coordinates
            self.updateSelectedPeak([chn1_peaksLocation, chn2_peaksLocation])

        # ----------- text box -----------
        # to be printed in lower right corner
        text_box_string = None

        if self.checkBox_fitLorentzian.isChecked():
            popt = self.fitMultipleLorentzians(xData=x_axis, yData=Avg_data[0], peaks_indices=Rb_peaks,
                                        peaks_init_width=(Rb_properties['widths'] * indx_to_time))  # just an attempt. this runs very slowly.
            params_text = self.multipleLorentziansParamsToText(popt)
            text_box_string = 'Calibration: \n' + str(self.indx_to_freq) +'\n'
            text_box_string += 'Found %d Lorentzians: \n'%len(Rb_peaks) + params_text

        # --------- plot ---------
        # Prepare data for display:
        labels = ["CH1 - Vortex Rb lines", "CH2 - Cavity transmission"]
        # peaksTags = self.peaks_tags if len(self.peaks_tags) == len(Rb_peaks) else [] # TODO: figure how to handle labels on peaks (if at all)
        peaksTags = []
        self.widgetPlot.plot_Scope(x_axis, Avg_data, autoscale=self.checkBox_plotAutoscale.isChecked(), redraw=redraw, labels = labels, x_ticks = x_ticks, y_ticks= y_ticks,
                                   aux_plotting_func = self.widgetPlot.plot_Scatter, scatter_y_data = np.concatenate([Avg_data[0][Rb_peaks], Avg_data[1][Cavity_peak]]),
                                   scatter_x_data = np.concatenate([x_axis[Rb_peaks], x_axis[Cavity_peak]]), scatter_tags = peaksTags,
                                   secondary_x_axis_func = secondary_x_axis_func, secondary_x_axis_label = 'Ferquency [MHz]', mark_peak = self.selectedPeaksXY,
                                   text_box = text_box_string)

        # --------- Lock -----------
        if self.lockOn and self.selectedPeaksXY and len(self.selectedPeaksXY) == 2: # if, and only if, we have selected two peaks to lock on
            errorDirection = 1 if self.checkBox_lockInverse.isChecked() else - 1
            errorSignal =  (self.selectedPeaksXY[1][0] - self.selectedPeaksXY[0][0]) *(errorDirection)
            # self.updatePID()
            output = self.pid(errorSignal)
            print('Error Signal: ', errorSignal, 'Output: ', output)
            # It's a problem with Red-Pitaya: to get 10V DC output, one has to set both Amp and Offset to 5V
            self.doubleSpinBox_ch1OutAmp.setValue(float(output) / 2)
            self.doubleSpinBox_ch1OutOffset.setValue(float(output) / 2)


        # -------- Save Data  --------:
        if self.checkBox_saveData.isChecked():
            self.saveCurrentDataClicked()

    def printPeaksInformation(self):
        print('printPeaksInformation', str(self.indx_to_freq))

    def fitMultipleLorentzians(self, xData, yData, peaks_indices, peaks_init_width):
        # -- fit functions ---
        def lorentzian(x, x0, a, gam):
            return a * gam ** 2 / (gam ** 2 + (x - x0) ** 2)

        def multi_lorentz_curve_fit(x, *params):
            shift = params[0]  # Scalar shift
            paramsRest = params[1:]  # These are the atcual parameters.
            assert not (len(paramsRest) % 3)  # makes sure we have enough params
            return shift + sum([lorentzian(x, *paramsRest[i: i + 3]) for i in range(0, len(paramsRest), 3)])

        # -------- Begin fit: --------------
        pub = [0.5, 1.5]  # peak_uncertain_bounds
        startValues = []
        for k, i in enumerate(peaks_indices):
            startValues += [xData[i], yData[i], peaks_init_width[k] / 2]
        lower_bounds = [-20] + [v * pub[0] for v in startValues]
        upper_bounds = [20] + [v * pub[1] for v in startValues]
        bounds = [lower_bounds, upper_bounds]
        startValues = [min(yData)] + startValues  # This is the constant from which we start the Lorentzian fits - ideally, 0
        popt, pcov = optimize.curve_fit(multi_lorentz_curve_fit, xData, yData, p0=startValues, maxfev=50000)
        #ys = [multi_lorentz_curve_fit(x, popt) for x in xData]
        return (popt)

    def multipleLorentziansParamsToText(self, popt):
        text = ''
        params = popt[1:] # first param is a general shift
        for i in range(0, len(params), 3):
            text += 'X_0' +' = %.2f; ' % params[i]
            text += 'I = %.2f; ' % params[i +1]
            text += 'gamma' + ' = %.2f \n' %  params[i + 2]
        return (text)
    def display_traces(self, data):
        self.rpfreqAxis = (np.arange(0, self.rp.bufferDuration * self.indx_to_freq[0], self.indx_to_freq[0])
                           - self.Rb_peaks[0] * self.indx_to_freq[0])
        self.rptimeAxis = np.arange(0, self.rp.bufferDuration / self.rp.sampling_rate, 1. / self.rp.sampling_rate) * 1e6
        truthiness = [self.checkBox_Rb_lines.isChecked(),
                      self.checkBox_Cavity_transm.isChecked()]
        labels = ["CH1 - Vortex Rb lines", "CH2 - Cavity transmission"]
        self.widgetPlot.plot_Cavity_Spec(data, self.rptimeAxis, self.rpfreqAxis, self.Rb_peaks, self.Rb_properties,
                                        self.indx_to_freq[0], truthiness, labels, cursors=None,
                                        autoscale=self.checkBox_plotAutoscale.isChecked())

    def acquire_traces_worker(self):
        if self.checkBox_Rb_lines.isChecked():
            worker = Worker(self.acquire_trace)
            self.print_to_dialogue("Acquiring trace...")
            worker.signals.finished.connect(self.acquire_trace_done)
            self.threadpool.start(worker)
        else:
            self.widgetPlot.plot([None])

    def acquire_trace(self, progress_callback):
        data = self.rp.get_traces()
        # dt = 1.0/(125e6/self.rp.decimation)
        # self.rptimes = np.arange(0, int(len(data[0])*dt), dt)
        self.widgetPlot.plot(data[0])

    def acquire_trace_done(self):
        self.print_to_dialogue("done")



if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Cavity_lock_GUI(simulation=simulation)
    window.show()
    app.exec_()
    sys.exit(app.exec_())