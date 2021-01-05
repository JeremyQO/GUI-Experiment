# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

To convert *.ui file to *.py:
!C:\\Users\\Jeremy\\anaconda3\\pkgs\\pyqt-impl-5.12.3-py38h885f38d_6\\Library\\bin\\pyuic5.bat -x .\\experiment.ui -o experiment.py
"""

from PyQt5 import uic
from PyQt5.QtWidgets import QTabWidget, QGridLayout, QMainWindow, QApplication, QLabel
from PyQt5.QtCore import QThreadPool
import os
from widgets.pgc import pgcWidget
from widgets.temperature import temperatureWidget

class experiment_gui(QMainWindow):
    def __init__(self, simulation=True):
        super(experiment_gui, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "main_GUI.ui")
        uic.loadUi(ui, self)
        
        # Add a tab widget:
        layout = QGridLayout()
        self.mainframe.setLayout(layout)
        self.mainframe.setContentsMargins(0,0,0,0)
        self.tabwidget = QTabWidget()
        self.tabwidget.setTabsClosable(True)
        self.tabwidget.setMovable(True)
        self.tabwidget.tabCloseRequested.connect(self.removeTab)
        layout.addWidget(self.tabwidget, 0, 0)
        layout.setContentsMargins(9,0, 9, 0)
        
        # Open widgets upon called action:
        self.actionPGC.triggered.connect(self.pgc_open_tab)
        self.actionTemperature.triggered.connect(self.temperature_open_tab)

        # Start Threadpool for multi-threading 
        self.simulation = simulation
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def pgc_open_tab(self):
        # if not hasattr(self, 'pgc_tab'):
        self.pgc_tab = pgcWidget.Pgc_gui(simulation=simulation)
        self.pgc_tab.threadpool = self.threadpool
        self.tabwidget.addTab(self.pgc_tab, "PGC")
            
    def temperature_open_tab(self):
        self.temperature_tab = temperatureWidget.Temperature_gui(simulation=simulation)
        self.temperature_tab.threadpool = self.threadpool
        self.tabwidget.addTab(self.temperature_tab,"Temperature")
        
    def removeTab(self, index):
        widget = self.tabwidget.widget(index)
        if widget is not None:
            widget.deleteLater()
        self.tabwidget.removeTab(index)
  
if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin()=='orelb' else True
    window = experiment_gui(simulation=simulation)
    window.show()
    # app.exec_()
    # sys.exit(app.exec_())