# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

"""

from PyQt5 import uic
from PyQt5.QtWidgets import QTabWidget, QGridLayout, QMainWindow, QApplication
from PyQt5.QtCore import QThreadPool
import os
from widgets.pgc import pgcWidget
from widgets.temperature import temperatureWidget
from widgets.od import ODWidget
from widgets.config_OPX import configWidget
import sys
sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


class Experiment_gui(QMainWindow):
    def __init__(self, simulation=True):
        super(Experiment_gui, self).__init__()
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
        # self.tabwidget.currentChanged.connect(self.tabchanged)
        layout.addWidget(self.tabwidget, 0, 0)
        layout.setContentsMargins(5,0, 5, 0)
        self.OPX = None
        
        # Open widgets upon called action:
        self.actionPGC.triggered.connect(self.pgc_open_tab)
        self.actionTemperature.triggered.connect(self.temperature_open_tab)
        self.actionOD.triggered.connect(self.OD_open_tab)
        self.actionConfigure.triggered.connect(self.conf_open_tab)

        # Start Threadpool for multi-threading 
        self.simulation = simulation
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def pgc_open_tab(self):
        if not hasattr(self, 'pgc_tab'):
            self.pgc_tab = pgcWidget.Pgc_gui(Parent=self, simulation=self.simulation)
            self.pgc_tab.threadpool = self.threadpool
            self.tabwidget.addTab(self.pgc_tab, "PGC")
            if self.OPX is not None :
                self.pgc_tab.enable_interface(True)
                self.pgc_tab.OPX = self.OPX
            
    def temperature_open_tab(self):
        if not hasattr(self, 'temperature_tab'):
            self.temperature_tab = temperatureWidget.Temperature_gui(Parent=self, simulation=self.simulation)
            self.temperature_tab.threadpool = self.threadpool
            self.tabwidget.addTab(self.temperature_tab,"Temperature")
            if self.OPX is not None :
                self.temperature_tab.enable_interface(True)
                self.temperature_tab.OPX = self.OPX
            
    def OD_open_tab(self):
        if not hasattr(self, 'OD_tab'):
            self.OD_tab = ODWidget.OD_gui(Parent=self, simulation=self.simulation)
            self.OD_tab.threadpool = self.threadpool
            self.tabwidget.addTab(self.OD_tab,"OD")
            if self.OPX is not None :
                self.OD_tab.enable_interface(True)
                self.OD_tab.OPX = self.OPX

    def conf_open_tab(self):
        if not hasattr(self, 'conf_tab'):
            # self.conf_tab = configWidget.ConfigGUI(Parent=self, simulation=self.simulation)
            self.conf_tab = configWidget.ConfigGUI()
            self.conf_tab.threadpool = self.threadpool
            self.tabwidget.addTab(self.conf_tab, "Configure")

    # def tabchanged(self, i):
    #     if hasattr(self, "temperature_tab") and hasattr(self, "pgc_tab"):
    #         if hasattr(self.temperature_tab, 'OPX') and (not hasattr(self.pgc_tab, 'OPX')):
    #             self.pgc_tab.OPX = self.temperature_tab.OPX
    #             self.pgc_tab.enable_interface(True)
    #             self.pgc_tab.print_to_dialogue("Grabbed OPX object from Temperature tab")
                
    #         if (not hasattr(self.temperature_tab, 'OPX')) and hasattr(self.pgc_tab, 'OPX'):
    #             self.temperature_tab.OPX = self.pgc_tab.OPX
    #             self.temperature_tab.enable_interface(True)
    #             self.temperature_tab.print_to_dialogue("Grabbed OPX object from PGC tab")
                
    #         if hasattr(self.temperature_tab, 'camera') and (not hasattr(self.pgc_tab, 'camera')):
    #             self.pgc_tab.camera = self.temperature_tab.camera
    #             self.pgc_tab.print_to_dialogue("Grabbed Camera object from Temperature tab")
                
    #         if (not hasattr(self.temperature_tab, 'OPX')) and hasattr(self.pgc_tab, 'OPX'):
    #             self.temperature_tab.camera = self.pgc_tab.camera
    #             self.temperature_tab.print_to_dialogue("Grabbed Camera object from PGC tab")    
        
    def removeTab(self, index):
        widget = self.tabwidget.widget(index)
        if widget is not None:
            widget.deleteLater()
            if widget.objectName() == 'Temperature':
                del self.temperature_tab
            if widget.objectName() == 'PGC':
                del self.pgc_tab
        self.tabwidget.removeTab(index)

if __name__=="__main__":
    import sys
    app = QApplication([])
    simulation = False if os.getlogin()=='orelb' else True
    window = Experiment_gui(simulation=simulation)
    window.show()
    app.exec_()
    # sys.exit(app.exec_())