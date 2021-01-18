# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop
"""

from redpitaya import redpitaya
import os
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

    def acquire_worker(self):
        if self.checkBox_ARM.isChecked():
            worker = Worker(self.acquire)
            worker.signals.finished.connect(lambda: self.print_to_dialogue("Stopped acquiring OD"))
            self.threadpool.start(worker)
    
    def acquire(self, progress_callback):
        while self.checkBox_ARM.isChecked():
            self.rp.acquire(decimation=1.0, duration=0.00001)
            res = self.rp.get_result()
            self.widgetPlot.plot(res[1])
     
    def OD_connect_worker(self):
        worker = Worker(self.OD_connect)
        self.pushButton_OD_Connect.setDisabled(True)
        worker.signals.finished.connect(lambda: self.pushButton_OD_Connect.setEnabled(True))
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def OD_connect(self, progress_callback):
        self.print_to_dialogue("Connecting to opx...")
        self.OPX = pgc()
        if hasattr(self, 'Parent'):
            self.Parent.OPX = self.OPX
        self.print_to_dialogue("Connected to opx")
        self.print_to_dialogue("Connecting to Red Pitaya...")
        # try:
        self.rp = redpitaya.RedPitaya()
        self.print_to_dialogue("Connected to Red Pitaya")
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