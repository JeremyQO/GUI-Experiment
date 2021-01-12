# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop

This class should be used as a parent to all the widgets of the various experiments
we want to run. 
"""

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox
import matplotlib
if matplotlib.get_backend()!='Qt5Agg':
    matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool
from datetime import datetime
import os
import widgets.temperature.dataplot as dataplot
from pyqtconsole.console import PythonConsole

class QuantumWidget (QWidget):
    def __init__(self, ui=None, simulation=True):
        super(QuantumWidget, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        uic.loadUi(ui, self)

        self.widgetPlot = dataplot.PlotWindow()
        self.verticalLayout_mpl.addWidget(self.widgetPlot.widgetPlot)
        self.simulation = simulation
        self.init_terminal()
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def init_terminal(self):
        self.console = PythonConsole()
        self.verticalLayout_terminal.addWidget(self.console)
        self.console.push_local_ns("o", self)
        self.console.eval_queued()
        self.frame_3.hide()
        self.checkBox_iPython.setEnabled(True)
        
    def showHideConsole(self):
        if self.checkBox_iPython.isChecked():
            self.frame_3.show()
        else:
            self.frame_3.hide()

    def print_to_dialogue (self, s):
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        self.listWidget_dialogue.addItem(dt_string+" - "+s)
        print(dt_string+" - "+s)
        self.listWidget_dialogue.scrollToBottom()
        
    def alert_box(self, message):
        m = QMessageBox()
        m.setText(message)
        m.setIcon(QMessageBox.Warning)
        m.setStandardButtons(QMessageBox.Ok)
        m.setDefaultButton(QMessageBox.Cancel)
        ret = m.exec_()

if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = QuantumWidget(ui="GUI-experiment\\widgets\\od", simulation=simulation)
    window.show()
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())