# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop
"""

from functions.od import scpi
import os
import numpy as np
from PyQt5.QtWidgets import QApplication
import matplotlib
from PyQt5.QtCore import QThreadPool
from widgets.worker import Worker
from calculate_OD import OD_exp
try:
    from OPXcontrol.pgc_macro_with_OD import pgc
except:
    print("Could not load pgc_macro_with_OD")
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
        
        self.checkBox_ARM.clicked.connect(self.acquire_worker)
        self.pushButton_OD_Connect.clicked.connect(self.OD_connect_worker)
        self.pushButton_acquire_OD.clicked.connect(self.getOD_worker)
        self.pushButton_update.clicked.connect(self.change_probe_frequency)
        self.enable_interface(False)

    def enable_interface(self, v):
        self.checkBox_ARM.setEnabled(v)
        self.pushButton_acquire_OD.setEnabled(v)
        self.frame_4.setEnabled(v)

    def change_probe_frequency(self):
        detuning = self.doubleSpinBox_frequency.value()
        self.OPX.qm.set_intermediate_frequency("AOM_2-3'",(93 + detuning)*1e6)
        self.print_to_dialogue("Detuning set to %.1f MHz"%(detuning))


    def getOD_worker(self):
        worker = Worker(self.getOD)
        self.print_to_dialogue("Acquiring OD...")
        self.pushButton_acquire_OD.setDisabled(True)
        worker.signals.finished.connect(self.get_OD_done)
        self.threadpool.start(worker)

    def get_OD_done(self):
        self.pushButton_acquire_OD.setEnabled(True)
        self.print_to_dialogue("OD acquired")

    def getOD(self, progress_callback, singleshot=True):
        if singleshot:
            self.OPX.MeasureOD(0)
        data = self.rp.get_trace(channel=2, trigger=1)
        times = np.arange(0, len(data) / self.rp.sampling_rate, 1. / self.rp.sampling_rate) * 1e6
        beamRadius = 200e-6
        wavelength = 780e-9
        cursors = list(np.array([6.8e-6, 2.6e-5, 4.65e-5, 6.57e-5]) * 1e6)
        self.odexp = OD_exp()
        OD = self.odexp.calculate_OD(beamRadius, times, cursors, data, wavelength)
        self.widgetPlot.plot_OD(times, data, cursors)
        self.print_to_dialogue("OD = %.2f"%(OD))
    
    def acquire_worker(self):
        if self.checkBox_ARM.isChecked():
            worker = Worker(self.acquire)
            self.print_to_dialogue("Acquiring OD...")
            self.pushButton_acquire_OD.setDisabled(True)
            worker.signals.finished.connect(self.acquire_done)
            self.threadpool.start(worker)

    def acquire_done(self):
        self.OPX.toggleMeasureODcontinuous(False)
        self.print_to_dialogue("Stopped acquiring OD")
        self.pushButton_acquire_OD.setEnabled(True)

    def acquire(self, progress_callback):
        self.OPX.toggleMeasureODcontinuous(True)
        while self.checkBox_ARM.isChecked():
            self.getOD(1, singleshot=False)
    
    def OD_connect_worker(self):
        worker = Worker(self.OD_connect)
        self.pushButton_OD_Connect.setDisabled(True)
        worker.signals.finished.connect(self.OD_connect_finished)
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def OD_connect_finished(self):
        self.enable_interface(True)
        self.pushButton_OD_Connect.setEnabled(True)

    def OD_connect(self, progress_callback):
        self.print_to_dialogue("Connecting to opx...")
        try:
            self.OPX = pgc()
            if hasattr(self, 'Parent'):
                self.Parent.OPX = self.OPX
            self.print_to_dialogue("Connected to opx")
        except NameError:
            self.print_to_dialogue("Couldn't connect to OPX")
        self.print_to_dialogue("Connecting to Red Pitaya...")
        try:
            self.rp = scpi.Redpitaya("132.77.55.19")
            self.print_to_dialogue("Connected to Red Pitaya")
        except TypeError:
            self.print_to_dialogue("Couldn't connect to RedPitaya")
        # except acquire.EDeviceManager:
        #     self.print_to_dialogue("Camera was already connected")
        # self.enable_interface(True)

if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = OD_gui(simulation=simulation)
    window.show()
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())