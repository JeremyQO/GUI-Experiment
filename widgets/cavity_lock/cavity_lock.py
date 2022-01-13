# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop
"""

from PyQt5 import uic
import time
from functions.od import RedPitayaWebsocket
from scipy import optimize
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
        self.rp = None  # Place holder
        self.signalLength = self.scope_parameters['OSC_DATA_SIZE']['value'] # 1024 by default
        # Rb Peaks
        self.Rb_peaks_default_value = [172, 259, 346, 409, 496, 646]
        self.Rb_peak_freq = [0, 36.1, 72.2, 114.6, 150.7, 229]
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
        self.widgetPlot.plot([None], [None])
        # self.rp = scpi.Redpitaya("rp-f08c22.local", trigger_delay=28e6, decimation=64)
        self.pushButton_utils_Connect.clicked.connect(self.utils_connect_worker)
        # self.pushButton_utils_Connect.clicked.connect(self.redPitayaConnect)
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)
        self.checkBox_Rb_lines.clicked.connect(self.chns_update)
        self.checkBox_Cavity_transm.clicked.connect(self.chns_update)
        # self.checkBox_Rb_lines.clicked.connect(self.acquire_traces_worker)
        self.pushButton_updatePlotDisplay.clicked.connect(self.updatePlotDisplay)
        self.checkBox_FreqScale.clicked.connect(self.chns_update)

        self.pushButton_updateFitParams.clicked.connect(self.update_plot_params)
        self.update_plot_params()

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


    def updatePlotDisplay(self):
        self.updateTriggerDelay()
        self.updateTimeScale()
        self.updateAveraging()

    def chns_update(self):
        self.CHsUpdated = True

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
        np.savez_compressed(os.path.join(todaydatadir, nowformated), CH1=self.Rb_lines_Avg_Data, CH2=self.Cavity_Transmission_Data, times=self.rptimes, meta=meta)

    def display_traces_worker(self):
        #worker = Worker(self.display_traces_loop)
        worker = Worker(self.redPitayaConnect) #Trying to work on a different thread...
        self.threadpool.start(worker)

    def redPitayaConnect(self, progress_callback):
        self.rp = RedPitayaWebsocket.Redpitaya(host="rp-f08c22.local", got_data_callback=self.update_scope, dialogue_print_callback = self.print_to_dialogue)
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


    # Never call this method. this is called by RedPitaya
    def update_scope(self, data, parameters):
        redraw = parameters['new_parameters'] or self.CHsUpdated  # This is true only when some parameters were changed on RP, prompting a total redraw of the plot (in other cases, updating the data suffices)
        if redraw:
            self.scope_parameters = parameters  # keep all the parameters. we need them.
            self.CHsUpdated = False
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
                                                           distance=float(self.spinBox_distance.text()),
                                                           prominence=float(self.doubleSpinBox_prominence.text()),
                                                           width=float(self.spinBox_width.text()))
        if self.checkBox_Cavity_transm.isChecked():
            self.Cavity_Transmission_Avg_Data = np.average(self.Cavity_Transmission_Data, axis=0)
            Avg_data = Avg_data + [self.Cavity_Transmission_Avg_Data]
            Transmission_peak, Transmission_properties = find_peaks(self.Cavity_Transmission_Avg_Data, prominence=float(
                                                                    self.doubleSpinBox_prominence.text()),
                                                                    width=float(self.spinBox_width.text()))
        # Rescale index to frequency detuning[MHz] from transition F=1->F'=0:
        # First - see if 6 peaks are found
        if len(Rb_peaks) != 6:
            Rb_peaks = self.Rb_peaks_default_value  # if not - use previous values
        else:
            self.Rb_peaks_default_value = Rb_peaks
        # self.indx_to_freq = 229/(Rb_peaks[-1]-Rb_peaks[0])
        # print(self.indx_to_freq)
        # print(Rb_peaks)
        # print(['%3.1f' %i for i in self.indx_to_freq * Rb_peaks-100.0])
        self.indx_to_freq = np.poly1d(np.polyfit(Rb_peaks, self.Rb_peak_freq, 1))  # TODO: should really use 5 poly?
        # TODO: any reason to keep the entire fit? seems only [0] is used.
        # print(np.polyfit(Rb_peaks, self.Rb_peak_freq, 5))
        # print(['%3.1f' %i for i in self.indx_to_freq(Rb_peaks)])
        print(Rb_peaks)
        # Save Data:
        if self.checkBox_saveData.isChecked():
            self.saveCurrentDataClicked()

        # ------- Scales -------
        # Set Values for x-axis frequency:
        time_scale = float(self.scope_parameters['OSC_TIME_SCALE']['value'])
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
        if self.checkBox_FreqScale.isChecked(): # if should add secondary axis
            secondary_x_axis_func = (timeToFreqScale, freqToTimeScale)
            # freq-scale
            # x_axis = (np.arange(0, len(Avg_data[0]) * self.indx_to_freq[0], self.indx_to_freq[0]) - Rb_peaks[0] * self.indx_to_freq[0])
            # x_ticks = np.linspace(x_axis[0] + Rb_peaks[0] * self.indx_to_freq[0], x_axis[-1], 10)
            # x_ticks = np.arange(x_axis[0], Rb_peaks[0] * self.indx_to_freq[0] * 10, Rb_peaks[0] * self.indx_to_freq[0])

        y_scale = float(self.doubleSpinBox_VtoDiv.text())
        y_offset = float(self.doubleSpinBox_VOffset.text())
        y_ticks = np.arange(y_offset - y_scale * 5, y_offset + y_scale * 5, y_scale)

        # --------- plot ---------
        # Prepare data for display:
        labels = ["CH1 - Vortex Rb lines", "CH2 - Cavity transmission"]
        peaks_tags = ['1-0', '1-0/1', '1-1', '1-0/2', '1-1/2', '1-2']
        # xaxis = np.linspace(0, 1024, 1024)
        # print(self.indx_to_freq(xaxis).shape)
        # print(Rb_peaks)
        # self.widgetPlot.plot_Scope(xaxis, [self.indx_to_freq(xaxis)], autoscale=self.checkBox_plotAutoscale.isChecked(),
        #                            redraw=redraw, aux_plotting_func = self.widgetPlot.plot_Scatter,
        #                            scatter_y_data = [self.indx_to_freq(Rb_peaks)], scatter_x_data = Rb_peaks)
        self.widgetPlot.plot_Scope(x_axis, Avg_data, autoscale=self.checkBox_plotAutoscale.isChecked(), redraw=redraw, labels = labels, x_ticks = x_ticks, y_ticks= y_ticks,
                                   aux_plotting_func = self.widgetPlot.plot_Scatter, scatter_y_data = Avg_data[0][Rb_peaks],scatter_x_data = x_axis[Rb_peaks], scatter_tags = peaks_tags,
                                   secondary_x_axis_func = secondary_x_axis_func, secondary_x_axis_label = 'Ferquency [MHz]')



        # self.Rb_lines_Avg_Data = np.average(self.Rb_lines_Avg_Data, axis=0)

        # # Rb_peak_freq_diff = [36.1, 36.1, 42.4, 36.1, 78.3]
        # Rb_peak_freq = [0, 36.1, 72.2, 114.6, 150.7, 229]
        # Rb_indx_diff = np.diff(self.Rb_peaks)
        # self.indx_to_freq = np.polyfit(self.Rb_peaks, Rb_peak_freq, 1)
        # for i in range(4):
        #     data = self.rp.get_traces()
        #     self.Rb_lines_Data = data[0]
        #     self.Rb_lines_Avg_Data = self.Rb_lines_Avg_Data + [self.Rb_lines_Data]
        #     self.Cavity_Transmission_Data = data[1]
        #
        # self.display_traces(data)
        # # self.Rb_lines_Avg_Data = []

    #
    # def display_traces_loop(self, progress_callback):
    #     while True:
    #         self.Rb_lines_Avg_Data = []
    #         data = self.rp.get_traces()
    #         self.Rb_lines_Data = data[0]
    #         self.Rb_lines_Avg_Data = self.Rb_lines_Avg_Data + [self.Rb_lines_Data]
    #         self.Cavity_Transmission_Data = data[1]
    #         self.Rb_lines_Avg_Data = np.average(self.Rb_lines_Avg_Data, axis=0)
    #         self.Rb_peaks, self.Rb_properties = find_peaks(self.Rb_lines_Avg_Data, distance=900, prominence=0.002, width=50)
    #         Transmission_peak, Transmission_properties = find_peaks(self.Cavity_Transmission_Data, prominence=0.005,
    #                                                                 width=1000)
    #         # Rb_peak_freq_diff = [36.1, 36.1, 42.4, 36.1, 78.3]
    #         Rb_peak_freq = [0, 36.1, 72.2, 114.6, 150.7, 229]
    #         Rb_indx_diff = np.diff(self.Rb_peaks)
    #         self.indx_to_freq = np.polyfit(self.Rb_peaks, Rb_peak_freq, 1)
    #         for i in range(4):
    #             data = self.rp.get_traces()
    #             self.Rb_lines_Data = data[0]
    #             self.Rb_lines_Avg_Data = self.Rb_lines_Avg_Data + [self.Rb_lines_Data]
    #             self.Cavity_Transmission_Data = data[1]
    #         self.display_traces(data)
    #         # self.Rb_lines_Avg_Data = []
    #         if self.checkBox_saveData.isChecked():
    #             self.saveCurrentDataClicked()


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

