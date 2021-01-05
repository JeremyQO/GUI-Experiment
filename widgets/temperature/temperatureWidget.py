# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui

To convert *.ui file to *.py:
!C:\\Users\\Jeremy\\anaconda3\\pkgs\\pyqt-impl-5.12.3-py38h885f38d_6\\Library\\bin\\pyuic5.bat -x .\\experiment.ui -o experiment.py
"""

import numpy as np
# from temperature_functions import images
from PyQt5 import uic
from PyQt5.QtWidgets import *
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool
# from gui_classes import Worker
import time
from datetime import datetime
try:
    import MvCamera
    from pgc_macro_with_OD import pgc
except:
    pass
import os

from functions.temperature.data_analysis import images
# import functions.pgc.control
import widgets.temperature.dataplot as dataplot
from widgets.worker import Worker 

class Temperature_gui (QWidget):
    def __init__(self, simulation=True):
        super(Temperature_gui, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "gui.ui")
        uic.loadUi(ui, self)
        
        self.widgetPlot = dataplot.PlotWindow()
        self.verticalLayout_mpl.addWidget(self.widgetPlot.widgetPlot)
        self.simulation = simulation
        if __name__=="__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
        # Connects:
        self.pushButton_temperature_Connect.clicked.connect(self.temperature_connect)
        self.pushButton_measure_temperature.clicked.connect(self.get_temperature_worker)

    def enable_interface(self,v=True):
        self.frame.setEnabled(v)
        self.listWidget_dialogue.setEnabled(v)
        self.frame_temperature.setEnabled(v)
        self.frame_temperature.setEnabled(v)
        
    def temperature_connect(self):
        # print("Success")
        self.pushButton_temperature_Connect.setDisabled(True)
        self.enable_interface(False)
        if self.simulation:
            dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\images'
            self.ims = images(dirname)  #, imrange=[0,5])
            self.print_to_dialogue("Images loaded successfully")
            self.enable_interface(True)
            self.pushButton_temperature_Connect.setEnabled(True)
            return

        self.print_to_dialogue("Connecting to OPX...")
        self.pgc_experiment = pgc()
        self.print_to_dialogue("Connected to OPX")
        self.print_to_dialogue("Connecting to Camera...")
        try:
            self.camera = MvCamera.MvCamera()
            self.print_to_dialogue("Connected to camera")
        except:
            self.print_to_dialogue("Camera already connected")

        self.enable_interface(True)
        self.pushButton_PGC_Connect.setEnabled(True)

    def get_temperature_worker(self):
        worker = Worker(self.get_temperature)
        worker.signals.finished.connect(lambda: self.print_to_dialogue("Done taking temperature"))
        self.threadpool.start(worker)

    def get_temperature(self, progress_callback):
        if self.simulation:
            N_snap = self.spinBox_N_temp.value()
            dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\images'
            self.ims = images(dirname)
            # _, *axs = self.ims.plot()
            self.widgetPlot.plotData(self.ims)
        else:
            self.camera.clear_folder()
            self.plot_continuous = False
            # self.set_enable(False)
            N_snap = self.spinBox_N_temp.value()
            self.sigmay = []
            self.sigmax = []
            self.pgc_experiment.measure_temperature(N_snap)
            for i in range(1, N_snap + 1):
                self.print_to_dialogue("Snap at %.2f ms" % (i))
                im, _ = self.camera.CaptureImage()
                imnp = np.asarray(im.convert(mode='L'), dtype=float)
                imim = temperature.image(imnp)
                ax, sx, sy = imim.optimizer([500, 1300, 500, 1100])
                self.sigmay.append(sy)
                self.sigmax.append(sx)
                self.plotData(imim)
                self.camera.SaveImageT(im, "%.2f" % (i))
    
            print("Taking background")
            self.pgc_experiment.Background()
            backgroundim, _ = self.camera.CaptureImage()
            self.background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
            self.camera.SaveImageT(backgroundim, 0, background=True)
    
            dirname = 'C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images'
            self.ims = images(dirname)
        
        

        # self.set_enable(True)
        # plt.figure()
        # self.ims.plot()
        # plt.show()
        # self.plot_continuous = True
        # return ims


    def print_to_dialogue (self, s):
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        self.listWidget_dialogue.addItem(dt_string+" - "+s)
        print(dt_string+" - "+s)
        self.listWidget_dialogue.scrollToBottom()
  
if __name__=="__main__":
    app = QApplication([])
    # ui_dir = "C:\\Users\\Jeremy\\Dropbox\\python_postdoc\\temperature\\GUI_qtdesigner.ui"
    if os.getlogin()=='orelb':
        ui_dir = "C:\\Pycharm\\Expriements\\QM\\temperature\\GUI_qtdesigner.ui"
        simulation = False
    elif os.getlogin()=='Jeremy':
        simulation = True
    window = Temperature_gui(simulation=simulation)
    window.show()
    window.temperature_connect()
    window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())