
from PyQt5 import uic
import time
from functions.od import RedPitayaWebsocket
from scipy import optimize,spatial
from scipy.signal import find_peaks
import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import matplotlib
from PyQt5.QtCore import QThreadPool
from datetime import date, datetime
from widgets.worker import Worker
import matplotlib.pyplot as plt
from functions.stirap.calculate_Nat_stirap import NAtoms
_CONNECTION_ATTMPTS = 2



Decimation_options = [1, 8, 64, 1024, 8192, 65536]

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
        self.signalLength = self.scope_parameters['OSC_DATA_SIZE']['value'] # 1024 by default

        # ---------- Rb Peaks ----------
        self.Rb_peaks_default_value = [172, 259, 346, 409, 496, 646]
        self.Rb_peak_freq = [0, 36.1, 72.2, 114.6, 150.7, 229]
        self.peaks_tags = ['1-0', '1-0/1', '1-1', '1-0/2', '1-1/2', '1-2']
        self.selectedPeakXY = None
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
        self.pushButton_StartLock.clicked.connect(self.updatePID)
        self.pushButton_selectPeak.clicked.connect(self.scopeListenForMouseClick)
        self.pushButton_calibratePeaks.clicked.connect(self.calibratePeaks)
        self.checkBox_FreqScale.clicked.connect(self.chns_update)
        self.checkBox_F1.clicked.connect(self.Rb_peak_freq_F1_update)
        self.checkBox_F2.clicked.connect(self.Rb_peak_freq_F2_update)
        self.pushButton_updateFitParams.clicked.connect(self.update_plot_params)
        self.update_plot_params()

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
        # self.rp.set_triggerSource('CH2')
        # self.print_to_dialogue("Trigger source CH2", color = 'red')
        t = float(self.doubleSpinBox_triggerDelay.text())
        self.rp.set_triggerDelay(t)
        self.print_to_dialogue("Trigger delay changed to %f ms" % t)

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
        self.rp.set_outputFunction(output = 1, function = int(self.doubleSpinBox_P.value()))
        self.rp.set_outputAmplitude(output = 1, v = float(self.doubleSpinBox_I.value()))
        self.rp.set_outputFrequency(output = 1, freq = float(self.doubleSpinBox_D.value()))

        print('Warning: connecting output via PID buttons. ask Natan.')

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
        # trigger_delay = int(self.spinBox_triggerDelay.text())
        # decimation = Decimation_options[self.comboBox_TimeScale.currentIndex()]
        # self.rp = RedPitayaWebsocket.Redpitaya(host = "rp-f08c22.local", got_data_callback = None)
        # self.print_to_dialogue("RedPitayas are connected.")
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
        np.savez_compressed(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data, CH2=self.Cavity_Transmission_Data, time=timeScale, meta=meta)

    def display_traces_worker(self):
        #worker = Worker(self.display_traces_loop)
        worker = Worker(self.redPitayaConnect) #Trying to work on a different thread...
        self.threadpool.start(worker)

    def redPitayaConnect(self, progress_callback):
        # self.rp = RedPitayaWebsocket.Redpitaya(host="rp-f08c22.local", got_data_callback=self.update_scope, dialogue_print_callback = self.print_to_dialogue)
        self.rp = RedPitayaWebsocket.Redpitaya(host="rp-f08c36.local", got_data_callback=self.update_scope, dialogue_print_callback=self.print_to_dialogue)
        if self.rp.connected:
            self.connection_attempt = 0 # connection
            self.print_to_dialogue("RedPitayas are connected.", color = 'green')
            self.updatePlotDisplay()
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
            # If clicked on canvas, stop listening for click
            self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseClickCID)
            self.listenForMouseClickCID = None
            # Find nearest peak
            self.selectedPeakXY = (event.xdata,event.ydata)
        if self.listenForMouseClickCID is None:  # start listening
            self.listenForMouseClickCID = self.widgetPlot.canvas.mpl_connect('button_press_event', mouseClickOnScope)
            self.selectedPeakXY = None
        else: # stop listen
            self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseClickCID)
            self.listenForMouseClickCID = None


    # Never call this method. this is called by RedPitaya
    def update_scope(self, data, parameters):
        redraw = parameters['new_parameters'] or self.CHsUpdated  # This is true only when some parameters were changed on RP, prompting a total redraw of the plot (in other cases, updating the data suffices)
        if redraw:
            self.scope_parameters = parameters  # keep all the parameters. we need them.
            self.CHsUpdated = False
            self.selectedPeakXY = None  # if it was necessary to redraw everything, peak will probably be lost
        self.Rb_lines_Data[self.avg_indx] = data[0]  # Insert new data
        self.Cavity_Transmission_Data[self.avg_indx] = data[1]  # Insert new data
        self.avg_indx = (self.avg_indx + 1) % self.Avg_num

        # Calculate avarage data and find peaks position (indx) and properties:
        # Avg_data = [np.average(self.Rb_lines_Data, axis=0), np.average(self.Cavity_Transmission_Data, axis=0)]
        Avg_data = []
        if self.checkBox_Rb_lines.isChecked():
            self.Rb_lines_Avg_Data = np.average(self.Rb_lines_Data, axis=0)
            Avg_data = Avg_data + [self.Rb_lines_Avg_Data]
            Rb_peaks, Rb_properties = find_peaks(self.Rb_lines_Avg_Data,
                                                           distance=float(self.spinBox_distance_ch1.text()),
                                                           prominence=float(self.doubleSpinBox_prominence_ch1.text()),
                                                           width=float(self.spinBox_width_ch1.text()))
        if self.checkBox_Cavity_transm.isChecked():
            self.Cavity_Transmission_Avg_Data = np.average(self.Cavity_Transmission_Data, axis=0)
            Avg_data = Avg_data + [self.Cavity_Transmission_Avg_Data]
            # Cavity_peak, Cavity_properties = find_peaks(self.Cavity_Transmission_Avg_Data,
            #                                                 distance=float(self.spinBox_distance_ch2.text()),
            #                                                 prominence=float(self.doubleSpinBox_prominence_ch2.text()),
            #                                                 width=float(self.spinBox_width_ch2.text()))

        # ---------------- Handle Rb Peaks ----------------
        # Rescale index to frequency detuning[MHz] from transition F=1->F'=0:
        # First - see if 6 peaks are found
        if len(Rb_peaks) != 6:
            Rb_peaks = self.Rb_peaks_default_value  # if not - use previous values
        else:
            self.Rb_peaks_default_value = Rb_peaks

        # -------------- Rb calibration, index to Frequency ---------------
        # print(['%3.1f' %i for i in self.indx_to_freq * Rb_peaks-100.0])
        if self.checkBox_liveCalibratePeaks.isChecked():
            self.indx_to_freq = np.poly1d(np.polyfit(Rb_peaks, self.Rb_peak_freq, 1))
            if self.calibrateRbPeaks:
                self.calibrateRbPeaks = False # only need to calibrate once.
                self.checkBox_liveCalibratePeaks.setChecked(False) # uncheck box.
                self.printPeaksInformation()

        # -------- Save Data  --------:
        if self.checkBox_saveData.isChecked():
            self.saveCurrentDataClicked()

        # ------- Scales -------
        # Set Values for x-axis frequency:
        time_scale = float(self.scope_parameters['OSC_TIME_SCALE']['value'])
        indx_to_time = float(10 * time_scale / self.scope_parameters['OSC_DATA_SIZE']['value'])
        # time-scale
        x_axis = np.linspace(0, time_scale * 10, num=int(self.scope_parameters['OSC_DATA_SIZE']['value']))
        x_ticks = np.arange(x_axis[0], x_axis[-1], time_scale)

        # Secondary axis
        indx_to_freq = self.indx_to_freq[0]
        def timeToFreqScale(t):
            return (t - Rb_peaks[0]) * indx_to_freq
        def freqToTimeScale(f):
            return f / indx_to_freq + Rb_peaks[0]

        secondary_x_axis_func = None
        if self.checkBox_FreqScale.isChecked():  # if should add secondary axis
            secondary_x_axis_func = (timeToFreqScale, freqToTimeScale)
            # freq-scale
            # x_axis = (np.arange(0, len(Avg_data[0]) * self.indx_to_freq[0], self.indx_to_freq[0]) - Rb_peaks[0] * self.indx_to_freq[0])
            # x_ticks = np.linspace(x_axis[0] + Rb_peaks[0] * self.indx_to_freq[0], x_axis[-1], 10)
            # x_ticks = np.arange(x_axis[0], Rb_peaks[0] * self.indx_to_freq[0] * 10, Rb_peaks[0] * self.indx_to_freq[0])

        y_scale = float(self.doubleSpinBox_VtoDiv.text())
        y_offset = float(self.doubleSpinBox_VOffset.text())
        y_ticks = np.arange(y_offset - y_scale * 5, y_offset + y_scale * 5, y_scale)

        # --------- select peak -----------
        if self.selectedPeakXY is not None:
            peaksLocation = np.array([[x_axis[p], Avg_data[0][p]] for p in Rb_peaks])  # all the peaks as coordinates
            nearestPeakIndex = spatial.KDTree(peaksLocation).query(self.selectedPeakXY)[1]
            nearestPeakLocation = peaksLocation[nearestPeakIndex]# [0] would have given us distance
            self.selectedPeakXY = nearestPeakLocation # update location of selected peak to BE the nearest peak
        # ----------- text box -----------
        # to be printed in lower right corner
        text_box_string = 'Text Box'
        # def lorentzian(p, x, y):
        #     x0, a, gam = p
        #     return  (a * gam ** 2 / (gam ** 2 + (x - x0) ** 2)) -
        # def lorentzian(x, x0, a, g, c = 0): # TODO: replace this with multiple lorentzians.
        #     print(x0, a, g)
        #     return c + a / (1 + ((x-x0)/g)**2)

        if self.checkBox_fitLorentzian.isChecked():
            # TODO: inverse signal? talk to Tal.

            popt = self.fitMultipleLorentzians(xData=x_axis, yData=Avg_data[0], peaks_indices=Rb_peaks,
                                        peaks_init_width=(Rb_properties['widths'] * indx_to_time))  # just an attempt. this runs very slowly.
            params_text = self.multipleLorentziansParamsToText(popt)
            text_box_string = 'Calibration: \n' + str(self.indx_to_freq) +'\n'
            text_box_string += 'Found %d Lorentzians: \n'%len(Rb_peaks) + params_text


        # --------- plot ---------
        # Prepare data for display:
        labels = ["CH1 - Vortex Rb lines", "CH2 - Cavity transmission"]
        # self.widgetPlot.plot_Scope(xaxis, [self.indx_to_freq(xaxis)], autoscale=self.checkBox_plotAutoscale.isChecked(),
        #                            redraw=redraw, aux_plotting_func = self.widgetPlot.plot_Scatter,
        #                            scatter_y_data = [self.indx_to_freq(Rb_peaks)], scatter_x_data = Rb_peaks)
        self.widgetPlot.plot_Scope(x_axis, Avg_data, autoscale=self.checkBox_plotAutoscale.isChecked(), redraw=redraw, labels = labels, x_ticks = x_ticks, y_ticks= y_ticks,
                                   aux_plotting_func = self.widgetPlot.plot_Scatter, scatter_y_data = Avg_data[0][Rb_peaks],scatter_x_data = x_axis[Rb_peaks], scatter_tags = self.peaks_tags,
                                   secondary_x_axis_func = secondary_x_axis_func, secondary_x_axis_label = 'Ferquency [MHz]', mark_peak = self.selectedPeakXY,
                                   text_box = text_box_string)

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