# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui

"""

import numpy as np
from PyQt5.QtWidgets import QApplication, QFileDialog
import matplotlib
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool, pyqtSlot
from datetime import date, datetime
try:
    import MvCamera
    from mvIMPACT import acquire
    from pgc_macro_with_OD import pgc
except:
    pass
import os

from functions.temperature.data_analysis import images, image
from widgets.worker import Worker

from widgets.quantumWidget import QuantumWidget


class ConfigGUI (QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        super(ConfigGUI, self).__init__(ui, simulation)
        self.checkBox_iPython.clicked.connect(self.showHideConsole)

        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())


if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = ConfigGUI(simulation=simulation)
    window.show()
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())