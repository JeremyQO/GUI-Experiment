# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui

"""

import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import *
import matplotlib
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool, pyqtSlot
from datetime import datetime
try:
    import MvCamera
    from mvIMPACT import acquire
    # from old.pgc_macro_Dor import pgc
    from pgc_macro_with_OD import pgc
except:
    pass
import os
from pyqtconsole.console import PythonConsole

from functions.temperature.data_analysis import images, image
import widgets.temperature.dataplot as dataplot
from widgets.worker import Worker
import sys

class Temperature_gui (QWidget):
    def __init__(self, simulation=True):
        super(Temperature_gui, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "gui.ui")
        uic.loadUi(ui, self)

        self.widgetPlot = dataplot.PlotWindow()
        self.verticalLayout_mpl.addWidget(self.widgetPlot.widgetPlot)
        self.init_terminal()
        self.simulation = simulation
        self.picturesDirName = None
        self.pixelCal = float(self.LineEdit_CalPixMM.text())
        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # Connects:
        self.pushButton_temperature_Connect.clicked.connect(self.temperature_connect_worker)
        self.pushButton_measure_temperature.clicked.connect(self.get_temperature_worker)
        self.pushButton_get_temperature_fromFolder.clicked.connect(self.get_temperature_from_dir)
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        # self.pushButtonBrowse.clicked.connect(self.browseSlot)
        
        # self.lineEdit_Folder.returnPressed.connect(self.returnPressedSlot)
        self.LineEdit_CalPixMM.returnPressed.connect(self.updateCal)
                
    def init_terminal(self):
        self.console = PythonConsole()
        self.verticalLayout_terminal.addWidget(self.console)
        self.console.push_local_ns("o", self)
        self.console.eval_queued()
        self.frame_3.hide()
        
    def showHideConsole(self):
        if self.checkBox_iPython.isChecked():
            self.frame_3.show()
        else:
            self.frame_3.hide()
        
    def updateCal(self):
        calibration =  self.LineEdit_CalPixMM.text()
        try:
            self.pixelCal = float(calibration)
            self.print_to_dialogue("Pixels per mm: %.1f"%(float(calibration)))
        except ValueError:
            m = QMessageBox()
            m.setText("Calibration must be float")
            m.setIcon(QMessageBox.Warning)
            m.setStandardButtons(QMessageBox.Ok)
            m.setDefaultButton(QMessageBox.Cancel)
            ret = m.exec_()
            self.lineEdit.setText("")
            self.refreshAll()
            self.debugPrint("Calibration must be float")

    def enable_interface(self,v=True):
        self.frame.setEnabled(v)
        self.frame_temperature.setEnabled(v)
        self.widget.setEnabled(v)
        # self.frame_temperature.setEnabled(v)

    def temperature_connect_worker(self):
        worker = Worker(self.temperature_connect)
        self.pushButton_temperature_Connect.setDisabled(True)
        worker.signals.finished.connect(lambda: self.pushButton_temperature_Connect.setEnabled(True))
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def temperature_connect(self, progress_callback):
        self.enable_interface(False)
        if self.simulation:
            dirname = "c:\\users\\orelb\\desktop\\mot_pgc_fall\\images" if os.getlogin() == 'orelb' else \
                'c:\\users\\jeremy\\desktop\\mot_pgc_fall\\images'
            self.ims = images(dirname)
            self.print_to_dialogue("images loaded successfully")
            self.enable_interface(True)
            self.pushButton_temperature_Connect.setEnabled(True)
            return

        self.print_to_dialogue("connecting to opx...")
        self.OPX = pgc()
        self.print_to_dialogue("connected to opx")
        self.print_to_dialogue("connecting to camera...")
        try:
            self.camera = MvCamera.MvCamera()
            self.print_to_dialogue("connected to camera")
        except acquire.EDeviceManager:
            self.print_to_dialogue("Camera was already connected")

        self.enable_interface(True)
        self.pushButton_temperature_Connect.setEnabled(True)

    def get_temperature_worker(self):
        worker = Worker(self.get_temperature)
        worker.signals.finished.connect(lambda: self.print_to_dialogue("Done taking temperature"))
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def progress_fn(self, n):
        self.progressBar.setValue(n)

    def get_temperature(self, progress_callback):
        if self.simulation:
            N_snap = self.spinBox_N_temp.value()
            dirname = 'C:\\Pycharm\\Expriements\\Instruments\\mvIMPACT_cam\\Images' if os.getlogin() == 'orelb' else \
                'c:\\users\\jeremy\\desktop\\mot_pgc_fall\\images'
            self.ims = images(dirname)
            # _, *axs = self.ims.plot()
            self.widgetPlot.plotData(self.ims)
            return

        self.camera.clear_folder()
        self.plot_continuous = False
        # self.set_enable(False)
        self.widgetPlot.sigmay = []
        self.widgetPlot.sigmax = []
        N_snap = self.spinBox_N_temp.value()
        self.OPX.measure_temperature(N_snap)
        for i in range(1, N_snap + 1):
            self.print_to_dialogue("Snap at %.2f ms" % (i))
            im, _ = self.camera.CaptureImage()
            imnp = np.asarray(im.convert(mode='L'), dtype=float)
            imim = image(imnp)
            ax, sx, sy = imim.optimizing([500, 1300, 500, 1100])
            self.widgetPlot.sigmay.append(sy)
            self.widgetPlot.sigmax.append(sx)
            self.widgetPlot.plotImages(imim)
            self.camera.SaveImageT(im, "%.2f" % (i))
            progress_callback.emit(i * 100 / N_snap)

        print("Taking background")
        self.OPX.Background()
        backgroundim, _ = self.camera.CaptureImage()
        self.background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        self.camera.SaveImageT(backgroundim, 0, background=True)

        dirname = 'C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images'
        self.ims = images(dirname)
        self.widgetPlot.plotData(self.ims)

    def print_to_dialogue (self, s):
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        f = lambda: print(dt_string+" - "+s)
        self.listWidget_dialogue.addItem(dt_string+" - "+s)
        print(dt_string+" - "+s)
        self.listWidget_dialogue.scrollToBottom()

    @pyqtSlot()
    def returnPressedSlot(self):
        dirname =  self.lineEdit_Folder.text()
        print(dirname)
        print(os.path.isdir(dirname))
        if os.path.isdir(dirname):
            self.picturesDirName = dirname
        else:
            m = QMessageBox()
            m.setText("Invalid folder name!\n" + dirname)
            m.setIcon(QMessageBox.Warning)
            m.setStandardButtons(QMessageBox.Ok)
            m.setDefaultButton(QMessageBox.Cancel)
            ret = m.exec_()
            self.lineEdit.setText("")
            self.refreshAll()
            self.debugPrint("Invalid file specified: " + fileName)

    @pyqtSlot()
    def browseSlot(self):
        dirname = QFileDialog().getExistingDirectory()
        self.lineEdit_Folder.setText(dirname)
        if os.path.isdir(dirname):
            self.picturesDirName = dirname
            self.pushButton_get_temperature_fromFolder.setEnabled(True)
            
    def get_temperature_from_dir(self):
        dirname = self.picturesDirName
        if os.path.isdir(dirname):
            self.ims = images(dirname)
            self.ims.pixelCal = self.pixelCal
            self.widgetPlot.plotData(self.ims)
            self.print_to_dialogue("Tx = %.2f uK, Ty = %.2f uK"%(self.ims.Tx*1e6, self.ims.Ty*1e6))
        

if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Temperature_gui(simulation=simulation)
    window.show()
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())