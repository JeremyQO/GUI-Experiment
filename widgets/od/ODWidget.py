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
try:
    from pgc_macro_with_OD import pgc
except:
    pass
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

    def getOD_worker(self):
        worker = Worker(self.getOD)
        self.print_to_dialogue("Acquiring OD...")
        worker.signals.finished.connect(lambda: self.print_to_dialogue("OD acquired"))
        self.threadpool.start(worker)
            
    def getOD(self, progress_callback):
        data = self.rp.get_trace(channel=2,trigger=1)
        self.widgetPlot.plot(np.arange(0,len(data)/self.rp.sampling_rate, 1./self.rp.sampling_rate), data)
    
    def acquire_worker(self):
        if self.checkBox_ARM.isChecked():
            worker = Worker(self.acquire)
            self.print_to_dialogue("Acquiring OD...")
            worker.signals.finished.connect(lambda: self.print_to_dialogue("Stopped acquiring OD"))
            self.threadpool.start(worker)
    
    def acquire(self, progress_callback):
        while self.checkBox_ARM.isChecked():
            res = self.rp.get_trace(channel=1,trigger=1)
            self.widgetPlot.plot(np.arange(0,len(res)/self.rp.sampling_rate, 1./self.rp.sampling_rate), res)
    
    def OD_connect_worker(self):
        worker = Worker(self.OD_connect)
        self.pushButton_OD_Connect.setDisabled(True)
        worker.signals.finished.connect(lambda: self.pushButton_OD_Connect.setEnabled(True))
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

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