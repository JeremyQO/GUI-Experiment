# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop
"""

from PyQt5 import uic
import time
from functions.od import scpi
from scipy import optimize
import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import matplotlib
from PyQt5.QtCore import QThreadPool
from datetime import date, datetime
from widgets.worker import Worker
from functions.stirap.calculate_Nat_stirap import NAtoms

try:
    from functions.od.calculate_OD import OD_exp
except:
    print("Run without calculate OD")
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')

from widgets.quantumWidget import QuantumWidget


class MWSpectroWidget(QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        ui_muwave_sequence = os.path.join(os.path.dirname(__file__), "MWSpectro_sequence.ui")  # if ui is None else ui
        super().__init__(ui, simulation)
        uic.loadUi(ui_muwave_sequence, self.frame_muwave_sequence)
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.widgetPlot.plot([None], [None])
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)
        self.continuous_display_traces = True  # Display the traces from RedPitaya continuously 

        self.pushButton_utils_Connect.clicked.connect(self.utils_connect_worker)
        self.pushButton_update.clicked.connect(self.change_probe_frequency)
        self.pushButton_Cursor.clicked.connect(self.positionCursorsList)
        self.pushButton_updateDecimation.clicked.connect(self.updateDecimation)
        self.pushButton_updateTriggerDelay.clicked.connect(self.updateTriggerDelay)
        self.checkBox_sequence.clicked.connect(self.showHideSequence)
        self.pushButton_saveCurrentData.clicked.connect(self.saveCurrentDataClicked)
        self.enable_interface(False)
        self.frame_muwave_sequence.hide()

        # MW spectroscopy parameters :
        # self.pushButton_update_MW_pulse_duration.clicked.connect(self.updateMWpulseDurationWorker)
        self.frame_muwave_sequence.doubleSpinBox_pulse_duration.editingFinished.connect(self.updateMWpulseDuration)
        self.frame_muwave_sequence.doubleSpinBox_detuning.editingFinished.connect(self.updateMWfrequencyDetuning)
        self.frame_muwave_sequence.doubleSpinBox_repetitions.editingFinished.connect(self.updateMWpulseRep)
        self.frame_muwave_sequence.pushButton_update_muwave.clicked.connect(self.updateParameters_sequence_workers)
        self.frame_muwave_sequence.pushButton_start_scan.clicked.connect(self.startScanWorker)

        # self.decimation = 8
        # self.cursors = list(np.array([145, 312, 535, 705]))
        self.cursors = []
        self.pulsesDelay = 0
        self.nathistory = []

        self.last_data1_OD, self.last_data2_OD = [], []
        self.last_data1_Sigma, self.last_data2_Sigma = [], []
        self.last_data1_Pi, self.last_data2_Pi = [], []
        self.last_data_CH1CH2Sum, self.last_data_Pi = [], []
        self.last_data_repump = []
        self.rptimes = []
        self.cursors_data = []
        self.datafile = None
        self.current_frequency = 0
        self.df = 0
        self.minf = 0
        self.maxf = 0
        self.rep = 4
        # self.enable_interface(True)

        self.odexp = OD_exp()
    
    def startScanWorker(self):
        worker = Worker(self.scanMW)
        worker.signals.finished.connect(self.scanMWfinished)
        # worker.signals.progress.connect(self.scanMWprogress)
        self.threadpool.start(worker)
        
    def scanMW(self, progress_callback):
        self.frame_muwave_sequence.pushButton_start_scan.setEnabled(False)
        minf = self.frame_muwave_sequence.doubleSpinBox_start_scan.value()
        maxf = self.frame_muwave_sequence.doubleSpinBox_stop_scan.value()
        df = self.frame_muwave_sequence.doubleSpinBox_d_f_scan.value()
        rep = self.frame_muwave_sequence.doubleSpinBox_repetitions.value()
        self.OPX.MW_spec_scan(minf, maxf, df, rep)
        self.df = df
        self.minf = minf
        self.maxf = maxf
        self.rep = rep
        self.OPX.update_parameters()
        
    def scanMWfinished(self):
        self.frame_muwave_sequence.pushButton_start_scan.setEnabled(True)
        self.print_to_dialogue("Starting Scan")
        self.current_frequency = self.minf
        
    # def scanMWprogress(self, n):
    #     self.frame_muwave_sequence.progressBar.setValue(n)
    
    def updateMWpulseDuration(self):
        duration = self.frame_muwave_sequence.doubleSpinBox_pulse_duration.value()
        self.OPX.MW_spec_MW_pulse_duration(int(duration))
            
    def updateMWfrequencyDetuning(self):
        det = self.frame_muwave_sequence.doubleSpinBox_detuning.value()
        self.OPX.MW_spec_detuning(int(det))
            
    def updateMWpulseRep(self):
        nrep = self.frame_muwave_sequence.doubleSpinBox_repetitions.value()
        self.OPX.MW_spec_Repetition_times(int(nrep))
    
    def updateParameters_sequence_workers(self):
        self.frame_muwave_sequence.pushButton_update_muwave.setEnabled(False)
        worker = Worker(self.updateParameters_sequence)
        worker.signals.finished.connect(self.update_stirap_sequence_done)
        self.threadpool.start(worker)

    def updateParameters_sequence(self, progress_callback):
        self.OPX.update_parameters()

    def update_stirap_sequence_done(self):
        self.print_to_dialogue("Parameters updated.")
        self.frame_muwave_sequence.pushButton_update_muwave.setEnabled(True)

    def showHideSequence(self):
        if self.checkBox_sequence.isChecked():
            self.frame_muwave_sequence.show()
        else:
            self.frame_muwave_sequence.hide()

    def updateDecimation(self):
        dec = int(self.comboBox_decimation.currentText())
        self.rp.set_decimation(dec)
        self.lineEdit_triggerDelay.setText(str(int(self.rp.triggerDelay) * 1e-3))
        self.print_to_dialogue("Decimation changed to %i" % dec)

    def updateTriggerDelay(self):
        t = int(float(self.lineEdit_triggerDelay.text()) * 1e3)
        self.rp.set_triggerDelay(t)
        self.print_to_dialogue("Trigger delay changed to %i ns" % t)

    def saveCurrentDataClicked(self):
        now = datetime.now()
        today = date.today()
        datadir = os.path.join("C:\\", "Pycharm", "Expriements", "DATA", "STIRAP")
        todayformated = today.strftime("%B-%d-%Y")
        todaydatadir = os.path.join(datadir, todayformated)
        nowformated = now.strftime("%Hh%Mm%Ss")
        try:
            os.makedirs(todaydatadir)
            self.print_to_dialogue("Created folder DATA/STIRAP/%s" % (todayformated))
            self.print_to_dialogue("Data Saved")
        except FileExistsError:
            self.print_to_dialogue("Data Saved")

        self.datafile = os.path.join(todaydatadir, nowformated + ".txt")
        meta = "Traces from the RedPitaya, obtained on %s at %s.\nMW_pulse_duration contains the duration of the MW pulse in us." % (todayformated, nowformated)

        # np.savetxt(self.datafile, np.transpose([self.rplastdata1, self.rplastdata2]),  fmt='%.6e', header=header)
        np.savez_compressed(os.path.join(todaydatadir, nowformated),
                            CH1_OD=self.last_data1_OD,
                            CH2_Depump=self.last_data2_OD,
                            CH1_Sigma=self.last_data1_Sigma,
                            CH2_Sigma=self.last_data2_Sigma,
                            CH1_Pi_Pi=self.last_data1_Pi,
                            CH2_Pi_repump=self.last_data_repump,
                            times=self.rptimes,
                            MW_pulse_duration=self.doubleSpinBox_MW_pulse_duration.value(),
                            MW_frequency=self.current_frequency,
                            meta=meta,
                            )

    def positionCursorsList(self):
        self.alert_box(
            "Turn of the B-field gradient and make sure that the pulses are properly contained within the plot.")
        boxText = str(self.comboBox_cursors.currentText())
        self.print_to_dialogue("Placing cursors around %s" % boxText)
        if boxText == "Sigma":
            dat = np.array(self.last_data_CH1CH2Sum)
        if boxText == "Pi":
            dat = np.array(self.last_data_Pi)
        if boxText == "Depump":
            dat = np.array(self.last_data2_OD)
        if boxText == "OD":
            dat = np.array(self.last_data1_OD)
        self.cursors = self.positionCursors(dat)
        Nat = NAtoms()
        self.pulsesDelay = Nat.get_delay(dat)

    def positionCursors(self, dat):
        nat = np.array(dat)
        dy = nat.max() - nat.min()
        tresholdlevel = nat.min() + dy / 2
        d_threshold = 150  # position before the threshold position on which we want to place the cursor
        a, b, d = 0, 0, 0
        for i, el in enumerate(nat):
            if el >= tresholdlevel:
                a = int(i - d_threshold)
                break
        for i, el in enumerate(nat[a + 100 + d_threshold:]):
            if el <= tresholdlevel:
                d = int(i)
                break
        for i, el in enumerate(nat[a + d + 400:]):
            if el >= tresholdlevel:
                b = int(i + a + d + 400 - d_threshold)
                break
        res = optimize.minimize(self.odexp.tominimizeNat, np.array([b]), args=(a, d, nat))
        print(res)
        b_opt = res.x[0]
        print([a, a + d, b_opt, b_opt + d])
        self.print_to_dialogue("Minimized down to Nat = %.0f * 1e3" % (res.fun / 1e3))
        added_interval = 5
        cursors = np.array([a, a + d, b_opt, b_opt + d]) / self.rp.sampling_rate * self.rp.decimation * 1e6
        cursors[1] += added_interval
        cursors[3] += added_interval
        Nat = NAtoms()
        self.CH1CH2delay = - Nat.get_delay(nat)
        return cursors

    def enable_interface(self, v):
        self.frame_4.setEnabled(v)
        self.frame_parameters.setEnabled(v)

    def change_probe_frequency(self):
        detuning = self.doubleSpinBox_frequency.value()
        self.OPX.qm.set_intermediate_frequency("AOM_2-3'", (93 + detuning) * 1e6)
        self.print_to_dialogue("Detuning set to %.1f MHz" % (detuning))

    def display_traces_worker(self):
        worker = Worker(self.display_traces_loop)
        self.threadpool.start(worker)

    def display_traces_loop(self, progress_callback):
        while self.continuous_display_traces:
            self.display_traces()

    def display_traces(self):
        data = self.rp.get_traces()
        dataPlot = [data[i] for i in range(len(data))]
        dataPlot[5] = data[4]
        dataPlot[4] = np.array(data[2]) + np.array(data[3])
        dataPlot.append(data[5])
        self.last_data1_OD, self.last_data2_OD = data[0], data[1]
        self.last_data1_Sigma, self.last_data2_Sigma = data[2], data[3]
        self.last_data1_Pi, self.last_data2_Pi = data[4], data[5]
        self.last_data_CH1CH2Sum, self.last_data_Pi = dataPlot[4], dataPlot[5]
        self.last_data_repump = self.last_data2_Pi
        self.rptimes = np.arange(0, self.rp.bufferDuration, 1. / self.rp.sampling_rate * self.rp.OD.decimation) * 1e6
        self.rptimes = np.linspace(0, self.rp.bufferDuration, len(self.last_data1_OD)) * 1e6
        truthiness = [self.checkBox_OD.isChecked(),
                      self.checkBox_Depump.isChecked(),
                      self.checkBox_CH1.isChecked(),
                      self.checkBox_CH2.isChecked(),
                      self.checkBox_CH1CH2Sum.isChecked(),
                      self.checkBox_Pi.isChecked(),
                      self.checkBox_Repump.isChecked(),
                      self.checkBox_Diff.isChecked(),
                      ]
        if self.checkBox_saveData.isChecked():
            self.saveCurrentDataClicked()
        boxText = str(self.comboBox_cursors.currentText())
        if boxText == "Sigma":
            self.cursors_data = np.array(self.last_data_CH1CH2Sum)
            avg_photons = 1.5
            sensitivity = 8998.0 / 2 + 8506.0 / 2
        if boxText == "Pi":
            self.cursors_data = np.array(self.last_data_Pi)
            avg_photons = 1.5
            sensitivity = 8476
        if boxText == "Depump":
            self.cursors_data = np.array(self.last_data2_OD)
            avg_photons = 2.0
            sensitivity = 8063
        if boxText == "OD":
            self.cursors_data = np.array(self.last_data1_OD)
            avg_photons = 2.0
            sensitivity = 75e3  # This is a h'irtut
        if self.checkBox_displayNat.isChecked():
            try:
                natoms = NAtoms()
                Nat = natoms.calculate_Nat(self.cursors, self.rptimes, trace=self.cursors_data, avg_photons=avg_photons,
                                           sensitivity=sensitivity)
                self.print_to_dialogue("Number of atoms = %.1f *1e6" % (Nat / 1e6))
                self.nathistory.append(Nat)
                if len(self.nathistory) > 30:
                    self.nathistory.pop(0)
            except IndexError:
                self.print_to_dialogue("Display Nat: List index out of range")
        dataPlot.append(self.cursors_data - np.roll(self.cursors_data, self.pulsesDelay))
        labels = ["OD", "Depump", "CH1", "CH2", "CH1+CH2", "Pi", "Repump", "Difference"]
        self.widgetPlot.plot_traces(dataPlot, self.rptimes, truthiness, labels, self.cursors,
                                    autoscale=self.checkBox_plotAutoscale.isChecked(), sensitivity=sensitivity,
                                    nathistory=self.nathistory)
        self.current_frequency += self.df*self.rep
        if self.current_frequency < self.maxf:
            self.print_to_dialogue("f = %.1f kHz" % (float(self.current_frequency)/1000))

    def utils_connect_worker(self):
        worker = Worker(self.utils_connect)
        self.pushButton_utils_Connect.setDisabled(True)
        worker.signals.finished.connect(self.utils_connect_finished)
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def utils_connect_finished(self):
        self.enable_interface(True)
        self.pushButton_utils_Connect.setEnabled(True)
        self.doubleSpinBox_MW_pulse_duration.setValue(self.OPX.Pulse_Length_MW)

    def utils_connect(self, progress_callback):
        self.print_to_dialogue("Connecting to RedPitayas...")
        trigger_delay = 170000
        self.lineEdit_triggerDelay.setText(str(trigger_delay * 1e-3))
        decimation = int(self.comboBox_decimation.currentText())
        self.rp = scpi.redPitayaCluster(trigger_delay=trigger_delay, decimation=decimation)
        self.print_to_dialogue("RedPitayas are connected.")
        time.sleep(0.1)
        self.connectOPX()
        # self.update_STIRAP_buttons_display()
        self.display_traces_worker()
        self.updateDecimation()
        self.updateTriggerDelay()


if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = MWSpectroWidget(simulation=simulation)
    window.show()
    app.exec_()
    sys.exit(app.exec_())

