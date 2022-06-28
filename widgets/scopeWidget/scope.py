
from PyQt5 import uic
import time
from functions import RedPitayaWebsocket
from scipy import optimize,spatial
from scipy.signal import find_peaks
# import vxi11 # https://github.com/python-ivi/python-vxi11
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

try:
    from functions.cavity_lock.cavity_lock import CavityLock
except:
    print("Run without calculate OD")
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')

from widgets.quantumWidget import QuantumWidget


class Scope_GUI(QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True, RedPitayaHost = None, debugging = False):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "scopeWidgetGUI.ui") if ui is None else ui
        self.host = RedPitayaHost
        self.debugging = debugging
        super().__init__(ui, simulation)
        # up to here, nothing to change.

        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.connection_attempt = 0  # This holds connection attmeps. As long as this is < than _CONNECTION_ATTMPTS, will try to reconnect
        self.scope_parameters = {'new_parameters': False, 'OSC_TIME_SCALE': {'value':'1'}, 'OSC_CH1_SCALE': {'value':'1'},'OSC_CH1_SCALE': {'value':'1'}, 'OSC_DATA_SIZE':{'value':1024}}
        self.CHsUpdated = False
        self.rp = None  # Place holder
        self.isSavingNDataFiles = False
        self.signalLength = self.scope_parameters['OSC_DATA_SIZE']['value'] # 1024 by default
        self.indx_to_freq = [0]

        # -- connect --
        self.connectButtonsAndSpinboxes()
        self.update_plot_params()

        self.utils_connect_worker()


    def connectButtonsAndSpinboxes(self):
        self.pushButton_utils_Connect.clicked.connect(self.utils_connect_worker)
        self.pushButton_saveCurrentData.clicked.connect(self.saveCurrentDataClicked)
        self.pushButton_updatePlotDisplay.clicked.connect(self.updatePlotDisplay)
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)
        self.checkBox_Rb_lines.clicked.connect(self.chns_update)
        self.checkBox_Cavity_transm.clicked.connect(self.chns_update)

        self.checkBox_CH1Inverse.clicked.connect(self.setInverseChns)
        self.checkBox_CH2Inverse.clicked.connect(self.setInverseChns)


    def setInverseChns(self):
        self.rp.set_inverseChannel(ch=1, value = self.checkBox_CH1Inverse.isChecked())
        self.rp.set_inverseChannel(ch=2, value =  self.checkBox_CH2Inverse.isChecked())

    def update_plot_params(self):
        self.Avg_num = int(self.spinBox_averaging.value())
        self.Rb_lines_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.Cavity_Transmission_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.avg_indx = 0

    def updateTriggerDelay(self):
        t = float(self.doubleSpinBox_triggerDelay.value())  # ms
        l = float(self.doubleSpinBox_triggerLevel.value()) # in mV
        s = self.comboBox_triggerSource.currentText() # text
        self.rp.set_triggerSource(s)
        self.rp.set_triggerDelay(t)
        self.rp.set_triggerLevel(l)
        # self.print_to_dialogue("Trigger delay changed to %f ms; Source: %s; Level: %2.f [V]" % (t,s,l))

    def updateTimeScale(self):
        t = float(self.doubleSpinBox_timeScale.text())
        self.rp.set_timeScale(t)
        # self.print_to_dialogue("Time scale changed to %f ms" % t)

    def updateAveraging(self):
        self.Avg_num = int(self.spinBox_averaging.value())
        self.Rb_lines_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.Cavity_Transmission_Data = np.zeros((self.Avg_num, self.signalLength))  # Place holder
        self.avg_indx = 0
        # self.print_to_dialogue("Data averaging changed to %i" % self.Avg_num)

    def updatePlotDisplay(self):
        self.updateTriggerDelay()
        self.updateTimeScale()
        self.updateAveraging()
        self.CHsUpdated = True

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
        self.isSavingNDataFiles = True

    def saveCurrentData(self, extra_text = ''):
        extra_text = str(extra_text)
        if self.isSavingNDataFiles: # if we are saving N files
            if self.spinBox_saveNFiles.value() > 1:
                self.spinBox_saveNFiles.setValue(self.spinBox_saveNFiles.value() - 1)  # decrease files to save by 1
            elif self.spinBox_saveNFiles.value() == 1:
                self.isSavingNDataFiles = False

        timeScale = np.linspace(0, float(self.scope_parameters['OSC_TIME_SCALE']['value']) * 10, num=int(self.scope_parameters['OSC_DATA_SIZE']['value']))
        now = datetime.now()
        today = date.today()
        # datadir = os.path.join("C:\\", "Pycharm", "Expriements", "DATA", "CavityLock")
        datadir = os.path.join("U:\\", "Lab_2021-2022", "Experiment_results", "Python Data")
        todayformated = today.strftime("%B-%d-%Y")
        todaydatadir = os.path.join(datadir, todayformated)
        nowformated = now.strftime("%H-%M-%S_%f")
        try:
            os.makedirs(todaydatadir)
            if not self.checkBox_saveData.isChecked():
                self.print_to_dialogue("Created folder Lab_2021-2022/Experiment_results/Python Data/%s" % (todayformated))
                self.print_to_dialogue("Data Saved")
        except FileExistsError:
            if not self.checkBox_saveData.isChecked():
                self.print_to_dialogue("Data Saved")

        self.datafile = os.path.join(todaydatadir, nowformated + ".txt")
        meta = "Traces from the RedPitaya, obtained on %s at %s.\n" % (todayformated, nowformated)
        cmnt = self.lineEdit_fileComment.text()
        # np.savez_compressed(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data, CH2=self.Cavity_Transmission_Data, time=timeScale, meta=meta)
        np.savez_compressed(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data,CH2=self.Cavity_Transmission_Avg_Data, time=timeScale, meta=meta, comment = cmnt, extra_text = extra_text)

    def redPitayaConnect(self, progress_callback):
        RpHost = ["rp-ffffb4.local","rp-f08c22.local", "rp-f08c36.local"]
        if self.host == None:
            self.rp = RedPitayaWebsocket.Redpitaya(host="rp-ffffb4.local", got_data_callback=self.update_scope,dialogue_print_callback=self.print_to_dialogue, debugging= self.debugging)
        else:
            self.rp = RedPitayaWebsocket.Redpitaya(host=self.host, got_data_callback=self.update_scope,
                                                   dialogue_print_callback=self.print_to_dialogue, debugging= self.debugging)

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


    # Never call this method. this is called by RedPitaya
    def update_scope(self, data, parameters):
        if self.rp.firstRun:
            # Set default from display...
            self.comboBox_triggerSource.setCurrentIndex(2) # Select EXT trigger...
            self.updatePlotDisplay()
            self.setInverseChns()
            self.showHideParametersWindow()
            self.chns_update()
            self.rp.firstRun = False

        # ---------------- Handle duplicate data ----------------
        # It seems RedPitaya tends to send the same data more than once. That is, although it has not been triggered,
        # scope will send current data as fast as it can.
        # Following lines aim to prevent unnecessary work
        previousDataIndex = (self.avg_indx - 1) % self.Avg_num
        if np.array_equal(self.Rb_lines_Data[previousDataIndex], data[0]) or np.array_equal(
                self.Cavity_Transmission_Data[previousDataIndex], data[1]):
            return
        # ---------------- Handle Redraws and data reading ----------------
        # This is true only when some parameters were changed on RP, prompting a total redraw of the plot (in other cases, updating the data suffices)
        redraw = (parameters['new_parameters'] or self.CHsUpdated)
        if redraw:
            self.scope_parameters.update(parameters)  # keep all the parameters. we need them.
            self.CHsUpdated = False
        self.Rb_lines_Data[self.avg_indx] = data[0]  # Insert new data
        self.Cavity_Transmission_Data[self.avg_indx] = data[1]  # Insert new data
        self.avg_indx = (self.avg_indx + 1) % self.Avg_num
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

        # ----------- text box -----------
        # to be printed in lower right corner
        text_box_string = None

        # --------- plot ---------
        # Prepare data for display:
        labels = ["CH1 - Vortex Rb lines", "CH2 - Cavity transmission"]
        self.widgetPlot.plot_Scope(x_axis, Avg_data, autoscale=self.checkBox_plotAutoscale.isChecked(), redraw=redraw, labels = labels, x_ticks = x_ticks, y_ticks= y_ticks,
                                   aux_plotting_func = self.widgetPlot.plot_Scatter, scatter_y_data = np.concatenate([Avg_data[0][Rb_peaks], Avg_data[1][Cavity_peak]]),
                                   scatter_x_data = np.concatenate([x_axis[Rb_peaks], x_axis[Cavity_peak]]),text_box = text_box_string)

        # -------- Save Data  --------:
        if self.checkBox_saveData.isChecked() or self.isSavingNDataFiles:
            self.saveCurrentData()


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



if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Scope_GUI(simulation=simulation)
    window.show()
    app.exec_()
    sys.exit(app.exec_())