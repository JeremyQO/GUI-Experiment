# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 12:17:08 2021

@author: Jeremy Raskop

This class should be used as a parent to all the widgets of the various experiments.
"""

import time
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QShortcut, QListWidgetItem
from PyQt5.QtGui import QKeySequence, QColor
import matplotlib
if matplotlib.get_backend()!='Qt5Agg':
    matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool
from datetime import datetime
import os
from widgets.worker import Worker
import widgets.temperature.dataplot as dataplot
from pyqtconsole.console import PythonConsole
# try:
# from OPXcontrol.OPX_control_New_v2 import OPX
from OPX_control_with_QuadRF import OPX
# except:
#     print("Could not load pgc_macro_with_OD")


class QuantumWidget (QWidget):
    def __init__(self, ui=None, simulation=True):
        super(QuantumWidget, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        uic.loadUi(ui, self)

        self.widgetPlot = dataplot.PlotWindow()
        
        try:
            self.verticalLayout_mpl.addWidget(self.widgetPlot.widgetPlot)
        except AttributeError:
            pass
        self.simulation = simulation
        self.init_terminal()
        self.checkBox_iPython.setEnabled(True)
        
        ui_parameters = os.path.join(os.path.dirname(__file__), "quantumWidgetParameters.ui")
        uic.loadUi(ui_parameters, self.frame_parameters)
        
        # self.paramsSc = QShortcut(QKeySequence('Ctrl+Space'), self)
        self.paramsSc = QShortcut(QKeySequence('F1'), self)
        self.paramsSc.activated.connect(self.checkCheckBoxParameters)
        self.iPython = QShortcut(QKeySequence('F2'), self)
        self.iPython.activated.connect(self.checkCheckBoxIpythonConsole)
        
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
            
        self.frame_parameters.checkBox_MOT_ON.clicked.connect(self.MOT_switch_connect)
        self.frame_parameters.checkBox_PGC_ON.clicked.connect(self.PGC_switch_connect)
        self.frame_parameters.checkBox_Fountain_ON.clicked.connect(self.Fountain_switch_connect)
        self.frame_parameters.checkBox_Imaging_ON.clicked.connect(self.Imaging_switch_connect)
        self.frame_parameters.checkBox_OD_ON.clicked.connect(self.OD_switch_connect)
        self.frame_parameters.checkBox_Depump_ON.clicked.connect(self.Depump_switch_connect)
        self.frame_parameters.checkBox_STIRAP_ON.clicked.connect(self.STIRAP_switch_connect)
        self.frame_parameters.checkBox_uwavespectro_ON.clicked.connect(self.uwavespectro_switch_connect)
        self.frame_parameters.pushButton_Update_FPGCAmp.clicked.connect(self.Update_FPGCAmp_connect)
        self.frame_parameters.pushButton_AOM_0_AMP.clicked.connect(self.update_fountain_AOM_0_amplitude_connect)
        self.frame_parameters.pushButton_AOM_P_AMP.clicked.connect(self.update_fountain_AOM_P_amplitude_connect)
        self.frame_parameters.pushButton_AOM_M_AMP.clicked.connect(self.update_fountain_AOM_M_amplitude_connect)
        self.frame_parameters.pushButton_snapTime.clicked.connect(self.snapTime_connect)
        self.frame_parameters.pushButton_CameraTriggerTime.clicked.connect(self.CameraTriggerTime_connect)
        self.frame_parameters.pushButton_Nshots.clicked.connect(self.Nshots_connect)
        self.frame_parameters.pushButton_OD_Time.clicked.connect(self.OD_Time_connect)
        self.frame_parameters.pushButton_DepumpTime.clicked.connect(self.DepumpTime_connect)
        self.frame_parameters.pushButton_DepumpAmp.clicked.connect(self.DepumpAmp_connect)
        self.frame_parameters.pushButton_FinalPGCFreq.clicked.connect(self.FinalPGCFreq_connect)
        self.frame_parameters.pushButton_UpdateAll.clicked.connect(self.updateParameters_workers)
        # update all

    def updateParameters_workers(self):
        self.frame_parameters.pushButton_UpdateAll.setEnabled(False)
        worker = Worker(self.updateParameters)
        worker.signals.finished.connect(self.updateParameters_done)
        self.threadpool.start(worker)

    def updateParameters(self, progress_callback):
        self.OPX.update_parameters()

    def updateParameters_done(self):
        self.print_to_dialogue("Parameters updated.")
        self.frame_parameters.pushButton_UpdateAll.setEnabled(True)

    def MOT_switch_connect(self):
        self.OPX.MOT_switch(self.frame_parameters.checkBox_MOT_ON.isChecked())
        
    def PGC_switch_connect(self):
        self.OPX.Linear_PGC_switch(self.frame_parameters.checkBox_PGC_ON.isChecked())
        
    def Fountain_switch_connect(self):
        self.OPX.Fountain_switch(self.frame_parameters.checkBox_Fountain_ON.isChecked())
        
    def Imaging_switch_connect(self):
        self.OPX.Imaging_switch(self.frame_parameters.checkBox_Imaging_ON.isChecked())
        
    def OD_switch_connect(self):
        self.OPX.OD_switch(self.frame_parameters.checkBox_OD_ON.isChecked())
        
    def Depump_switch_connect(self):
        self.OPX.Depump_switch(self.frame_parameters.checkBox_Depump_ON.isChecked())

    def STIRAP_switch_connect(self):
        # self.OPX.STIRAP_switch(self.frame_parameters.checkBox_STIRAP_ON.isChecked())
        self.OPX.STIRAP_operation_switch(self.frame_parameters.checkBox_STIRAP_ON.isChecked())
        
    def uwavespectro_switch_connect(self):
        self.OPX.MW_switch(self.frame_parameters.checkBox_uwavespectro_ON.isChecked())

    def FinalPGCFreq_connect(self):
        f = self.frame_parameters.doubleSpinBox_FinalPGCFreq.value()
        self.OPX.update_pgc_final_freq(f*1e6)

    def Update_FPGCAmp_connect(self):
        a = self.frame_parameters.doubleSpinBox_Update_FPGCAmp.value()
        self.OPX.update_lin_pgc_final_amplitude(a)

    def update_fountain_AOM_0_amplitude_connect(self):
        a = self.frame_parameters.doubleSpinBox_AOM_0_AMP.value()
        self.OPX.update_fountain_AOM_0_amplitude(a)
        
    def update_fountain_AOM_P_amplitude_connect(self):
        a = self.frame_parameters.doubleSpinBox_AOM_P_AMP.value()
        self.OPX.update_fountain_AOM_plus_amplitude(a) 
    
    def update_fountain_AOM_M_amplitude_connect(self):
        a = self.frame_parameters.doubleSpinBox_AOM_M_AMP.value()
        self.OPX.update_fountain_AOM_minus_amplitude(a) 
    
    def snapTime_connect(self):
        s = self.frame_parameters.doubleSpinBox_snapTime.value()
        self.OPX.update_snap_time(s)
        
    def CameraTriggerTime_connect(self):
        t = self.frame_parameters.doubleSpinBox_CameraTriggerTime.value()
        self.OPX.update_camera_trig_time(t)
        
    def Nshots_connect(self):
        n = self.frame_parameters.spinBox_Nshots.value()
        self.OPX.Film_graber(n)
        
    def OD_Time_connect(self):
        t = self.frame_parameters.doubleSpinBox_OD_Time.value()
        self.OPX.MeasureOD(t)
        
    def DepumpTime_connect(self):
        t = self.frame_parameters.doubleSpinBox_DepumpTime.value()
        self.OPX.MeasureNatoms(t)
        
    def DepumpAmp_connect(self):
        a = self.frame_parameters.doubleSpinBox_DepumpAmp.value()
        self.OPX.doubleSpinBox_DepumpAmp(a)

    def init_terminal(self):
        self.console = PythonConsole()
        self.verticalLayout_terminal.addWidget(self.console)
        self.console.push_local_ns("o", self)
        self.console.eval_queued()
        self.frame_3.hide()
        # self.frame_parameters.hide()
        self.checkBox_iPython.setEnabled(True)

    def checkCheckBoxParameters(self):
        s = self.checkBox_parameters.isChecked()
        self.checkBox_parameters.setChecked(not s)
        self.showHideParametersWindow()

    def showHideParametersWindow(self):
        if self.checkBox_parameters.isChecked():
            self.frame_parameters.show()
        else:
            self.frame_parameters.hide()

    def checkCheckBoxIpythonConsole(self):
        s = self.checkBox_iPython.isChecked()
        self.checkBox_iPython.setChecked(not s)
        self.showHideConsole()

    def showHideConsole(self):
        if self.checkBox_iPython.isChecked():
            self.frame_3.show()
        else:
            self.frame_3.hide()

    def print_to_dialogue (self, s, color = 'black'):
        s = str(s)
        if color not in ['black','green','red','blue']:
            color = 'black'
            s = s + ' You must choose colour from: %s' %str(color)
        dt_string =  datetime.now().strftime("%H:%M:%S")
        listItem = QListWidgetItem(dt_string+" - "+s)
        listItem.setForeground(QColor(color))
        self.listWidget_dialogue.addItem(listItem)
        print(dt_string+" - "+s)
        self.listWidget_dialogue.scrollToBottom()

    def alert_box(self, message):
        m = QMessageBox()
        m.setText(message)
        m.setIcon(QMessageBox.Warning)
        m.setStandardButtons(QMessageBox.Ok)
        m.setDefaultButton(QMessageBox.Cancel)
        ret = m.exec_()

    def connectOPX(self):
        self.print_to_dialogue("Connecting to OPX...")
        try:
            if hasattr(self, 'Parent'):
                if self.Parent.OPX is not None:
                    self.OPX = self.Parent.OPX
                    self.print_to_dialogue("Grabbed OPX from parent")
                else:
                    self.OPX = OPX()
                    self.Parent.OPX = self.OPX
                    self.print_to_dialogue("Connected to OPX")
            else:
                self.OPX = OPX()
                self.print_to_dialogue("Connected to OPX")
        except NameError:
            self.print_to_dialogue("Couldn't connect to OPX")
        #self.frame_parameters.doubleSpinBox_Update_FPGCAmp.setValue(self.OPX.PGC_final_amp)
        #self.frame_parameters.doubleSpinBox_FinalPGCFreq.setValue(self.OPX.IF_TOP1_PGC*1e-6)



if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = QuantumWidget(ui="GUI-experiment\\widgets\\od", simulation=simulation)
    window.show()
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())