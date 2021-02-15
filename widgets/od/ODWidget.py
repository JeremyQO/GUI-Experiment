# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop
"""

from functions.od import scpi
import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import matplotlib
from PyQt5.QtCore import QThreadPool
from widgets.worker import Worker
try:
    from calculate_OD import OD_exp
except:
    print("Run without calculate OD")

if matplotlib.get_backend()!='Qt5Agg':
    matplotlib.use('Qt5Agg')

from widgets.quantumWidget import QuantumWidget

class OD_gui (QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        super().__init__(ui, simulation)
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.widgetPlot.plot([None], [None])
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)
        
        self.checkBox_OD_continuous.clicked.connect(self.acquire_OD_worker)
        self.checkBox_Nat_continuous.clicked.connect(self.acquire_Nat_worker)
        self.pushButton_utils_Connect.clicked.connect(self.utils_connect_worker)
        self.pushButton_singleshot_OD.clicked.connect(self.get_OD_worker)
        self.pushButton_update.clicked.connect(self.change_probe_frequency)
        self.pushButton_ODtimes.clicked.connect(self.change_OD_measure_time)
        self.pushButton_DepumpAmp.clicked.connect(self.change_Nat_Amp)
        self.pushButton_NatTime.clicked.connect(self.change_depumper_time)
        self.pushButton_singleshot_Nat.clicked.connect(self.get_Nat_worker)
        self.enable_interface(False)

        self.decimation = 8
        self.cursorsOD = list(np.array([145, 312, 535, 705])/ 8 * self.decimation)
        self.cursorsNat = list(np.array([64,208,452,611])/ 8 * self.decimation)

    

    def enable_interface(self, v):
        self.checkBox_OD_continuous.setEnabled(v)
        self.pushButton_singleshot_Nat.setEnabled(v)
        self.checkBox_Nat_continuous.setEnabled(v)
        self.pushButton_singleshot_OD.setEnabled(v)
        self.frame_4.setEnabled(v)
        # self.checkBox_parameters.setEnabled(v)
        self.frame_parameters.setEnabled(v)

    def change_Nat_Amp(self):
        newamp = self.doubleSpinBox_DepumpAmp.value()
        self.OPX.setMeasureNatomsAmp(newamp)
        self.print_to_dialogue("Depump relative amplitude set to %.2f"%(newamp))

    def change_depumper_time(self):
        dtime = self.doubleSpinBox_NatTime.value()
        self.OPX.MeasureNatoms(dtime)
        self.print_to_dialogue("Measuring Nat at %.2f ms"%(dtime))

    def change_probe_frequency(self):
        detuning = self.doubleSpinBox_frequency.value()
        self.OPX.qm.set_intermediate_frequency("AOM_2-3'",(93 + detuning)*1e6)
        self.print_to_dialogue("Detuning set to %.1f MHz"%(detuning))

    def change_OD_measure_time(self):
        odtime = self.doubleSpinBox_ODtimes.value()
        self.OPX.MeasureOD(odtime)
        self.print_to_dialogue("Measuring OD at %.2f ms"%(odtime))

    def get_OD_worker(self):
        worker = Worker(self.get_OD)
        self.print_to_dialogue("Acquiring OD...")
        self.pushButton_singleshot_OD.setDisabled(True)
        worker.signals.finished.connect(self.get_OD_done)
        self.threadpool.start(worker)

    def get_OD_done(self):
        self.pushButton_singleshot_OD.setEnabled(True)
        self.print_to_dialogue("OD acquired")

    def get_OD(self, progress_callback, singleshot=True):
        if singleshot:
            odtime = self.doubleSpinBox_ODtimes.value()
            self.OPX.MeasureOD(odtime)
        # data = self.rp.get_trace(channel=2)
        data1, data2 = self.rp.get_traces()
        times = np.arange(0, len(data1) / self.rp.sampling_rate, 1. / self.rp.sampling_rate) * 1e6
        beamRadius = 200e-6
        wavelength = 780e-9
        self.odexp = OD_exp()
        OD = self.odexp.calculate_OD(beamRadius, times, self.cursorsOD, data1, wavelength)
        self.widgetPlot.plot_OD(times, data1, data2, self.cursorsOD, autoscale=self.checkBox_plotAutoscale.isChecked())
        self.print_to_dialogue("OD = %.2f"%(OD))

    def acquire_OD_worker(self):
        if self.checkBox_OD_continuous.isChecked():
            worker = Worker(self.acquire_OD)
            self.print_to_dialogue("Acquiring OD...")
            self.pushButton_singleshot_OD.setDisabled(True)
            worker.signals.finished.connect(self.acquire_OD_done)
            self.threadpool.start(worker)

    def acquire_OD_done(self):
        self.OPX.toggleMeasureODcontinuous(False)
        self.print_to_dialogue("Stopped acquiring OD")
        self.pushButton_singleshot_OD.setEnabled(True)

    def acquire_OD(self, progress_callback):
        self.OPX.toggleMeasureODcontinuous(True)
        while self.checkBox_OD_continuous.isChecked():
            self.get_OD(1, singleshot=False)

    def get_Nat_worker(self):
        worker = Worker(self.get_Nat)
        self.print_to_dialogue("Acquiring number of atoms...")
        self.pushButton_singleshot_Nat.setDisabled(True)
        worker.signals.finished.connect(self.get_Nat_done)
        self.threadpool.start(worker)

    def get_Nat_done(self):
        self.pushButton_singleshot_Nat.setEnabled(True)
        self.print_to_dialogue("Number of atoms acquired")

    def get_Nat(self, progress_callback, singleshot=True):
        if singleshot:
            self.OPX.MeasureNatoms(0)
        # data = self.rp.get_trace(channel=1)
        data1, data2 = self.rp.get_traces()
        times = np.arange(0, len(data1) / self.rp.sampling_rate, 1. / self.rp.sampling_rate) * 1e6

        # self.odexp = OD_exp()
        # OD = self.odexp.calculate_OD(beamRadius, times, self.cursorsOD, data, wavelength)
        self.widgetPlot.plot_OD(times, data1, data2, self.cursorsNat, autoscale=self.checkBox_plotAutoscale.isChecked())
        # self.print_to_dialogue("OD = %.2f"%(OD))

    def acquire_Nat_worker(self):
        if self.checkBox_Nat_continuous.isChecked():
            worker = Worker(self.acquire_Nat)  #
            self.print_to_dialogue("Acquiring number of atoms...")
            self.pushButton_singleshot_OD.setDisabled(True)
            worker.signals.finished.connect(self.acquire_Nat_done)  #
            self.threadpool.start(worker)

    def acquire_Nat(self, progress_callback):
        self.OPX.toggleMeasureNatomscontinuous(True)
        while self.checkBox_Nat_continuous.isChecked():
            self.get_Nat(1, singleshot=False)

    def acquire_Nat_done(self):
        self.OPX.toggleMeasureNatomscontinuous(False)
        self.print_to_dialogue("Stopped acquiring number of atoms")
        self.pushButton_singleshot_OD.setEnabled(True)

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
        self.print_to_dialogue("Connecting to Red Pitaya...")
        try:
            self.rp = scpi.Redpitaya("132.77.55.19", decimation=self.decimation)
            self.print_to_dialogue("Connected to Red Pitaya")
        except TypeError:
            self.print_to_dialogue("Couldn't connect to Red Pitaya")
        
        self.connectOPX()


if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = OD_gui(simulation=simulation)
    window.show()
    app.exec_()
    sys.exit(app.exec_())

