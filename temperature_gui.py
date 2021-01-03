# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui
* Make fucntion class inherit the main window class that contains the *.ui

To convert *.ui file to *.py:
!C:\\Users\\Jeremy\\anaconda3\\pkgs\\pyqt-impl-5.12.3-py38h885f38d_6\\Library\\bin\\pyuic5.bat -x .\\experiment.ui -o experiment.py
"""

import numpy as np
import sys
from temperature_functions import images
# import matplotlib.pylab as plt
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool
from gui_classes import PlotWindow, WorkerSignals, Worker
import time
from datetime import datetime
import PIL as pil
try:
    import MvCamera
    import temperature
    from pgc_macro_with_OD import pgc
except:
    pass
import os
import matplotlib.pyplot as plt

"""
* Maybe this PGC_tab class could be the one inheriting from PlotWindow.
* Make a 'widgets' folder, with a single file for a single tab (such as 
    temperature, PGC, ...).
"""

# class PGC_tab(experiment_gui):
#     pass

class experiment_gui (PlotWindow):
    def __init__(self, ui, simulation=True):
        self.simulation = simulation
        super(experiment_gui, self).__init__()
        Form, Window = uic.loadUiType(ui)
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.form.verticalLayout_mpl.addWidget(self.widgetPlot)
        # self.form.verticalLayout_mpl_temperature.addWidget(self.widgetPlot_temp)
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # self.form.actionPGC.triggered.connect(lambda: self.print_to_dialogue("PGC"))


        # Connects:

        self.form.tabWidget.tabCloseRequested.connect(self.close_tab)

        self.form.pushButton_PGC_Connect.clicked.connect(self.PGC_connect)
        self.form.pushButton_temperature_Connect.clicked.connect(self.PGC_connect)
        self.form.pushButton_updateSnapTime.clicked.connect(self.update_Snaptime)
        self.form.pushButton_update_dA.clicked.connect(self.update_dA)
        self.form.pushButton_update_df.clicked.connect(self.update_df)
        self.form.pushButton_measure_temperature.clicked.connect(self.get_temperature_worker)
        self.form.checkBox_plotContinuous.clicked.connect(self.take_continuous_pictures_worker)
        self.form.pushButton_takeBackground.clicked.connect(self.take_new_background_worker)


    def set_enable(self,v=True):
        self.form.frame_3.setEnabled(v)
        self.form.checkBox_plotContinuous.setEnabled(v)
        self.form.frame.setEnabled(v)
        self.form.frame_5.setEnabled(v)
        self.form.pushButton_takeBackground.setEnabled(v)
        self.form.frame_temperature.setEnabled(v)
    def PGC_connect(self):
        # print("Success")
        self.form.pushButton_temperature_Connect.setDisabled(True)
        self.form.pushButton_PGC_Connect.setDisabled(True)
        self.form.checkBox_plotContinuous.setDisabled(True)
        if self.simulation:
            dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\images'
            self.ims = images(dirname)  #, imrange=[0,5])
            self.print_to_dialogue("Images loaded successfully")
            self.set_enable(True)
            self.form.pushButton_temperature_Connect.setEnabled(True)
            self.form.pushButton_PGC_Connect.setEnabled(True)
            return

        # self.form.checkBox_backgroundTaken.setEnabled(True)
        self.print_to_dialogue("Connecting to OPX...")
        self.pgc_experiment = pgc()
        self.print_to_dialogue("Connected to OPX")
        self.print_to_dialogue("Connecting to Camera...")
        try:
            self.camera = MvCamera.MvCamera()
            self.print_to_dialogue("Connected to camera")
        except:
            self.print_to_dialogue("Camera already connected")

        # Todo: add background taken button and green light
        # backgroundim = pil.Image.open('background_23-12-2020.png')
        self.set_enable(True)
        self.form.pushButton_temperature_Connect.setEnabled(True)
        self.form.pushButton_PGC_Connect.setEnabled(True)

    def update_Snaptime(self):
        v = self.form.doubleSpinBox_Snap.value()
        if self.simulation:
            self.print_to_dialogue("Updated snaptime to %.2f" % (v))
            return
        self.pgc_experiment.update_snap_time(float(v))
        self.print_to_dialogue("Updated snaptime to %.2f" % (v))
        
    def update_dA(self):
        v = self.form.doubleSpinBox_dA.value()
        if self.simulation:
            self.print_to_dialogue("Updated dA to %.3f"%(v))
            return
        self.pgc_experiment.update_da(v)
        self.print_to_dialogue("Updated dA to %.3f" % (v))

    def update_df(self):
        v = self.form.doubleSpinBox_df.value()
        if self.simulation:
            self.print_to_dialogue("Updated df to %.3f"%(v))
            return
        self.pgc_experiment.update_df_pgc(v)
        self.print_to_dialogue("Updated df to %.3f" % (v))

    # def measure_temperature(self):
    #     start = self.form.doubleSpinBox_start_temp.value()
    #     stop = self.form.doubleSpinBox_end_temp.value()
    #     N = self.form.spinBox_N_temp.value()
    #     # self.print_to_dialogue("Taking %i pictures, from %.2f to %.2f"%(N, start, stop))
    #     self.print_to_dialogue("Temperature [%.2f, %.2f, %i]"%(start, stop, N))


    def take_new_background_worker(self):
        worker = Worker(self.take_new_background)
        worker.signals.finished.connect(lambda: self.print_to_dialogue("New background taken"))
        self.threadpool.start(worker)

    def take_new_background(self, progress_callback):
        # todo: get background. what happens if camera roll is true when clicked ?
        if self.simulation :
            self.form.checkBox_substractBackground.setEnabled(True)
            return

        self.print_to_dialogue("Snapping Background...")
        self.pgc_experiment.Background()
        backgroundim, _ = self.camera.CaptureImage()
        self.background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        self.form.checkBox_substractBackground.setEnabled(True)


    def print_to_dialogue (self, s):
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        self.form.listWidget.addItem(dt_string+" - "+s)
        self.form.listWidget_temp.addItem(dt_string+" - "+s)
        print(dt_string+" - "+s)
        self.form.listWidget.scrollToBottom()
        self.form.listWidget_temp.scrollToBottom()

    def close_tab(self,index):
      self.form.tabWidget.removeTab(index)
      print(index)
      


    def get_temperature_worker(self):
        worker = Worker(self.get_temperature)
        worker.signals.finished.connect(lambda: self.print_to_dialogue("Done taking temperature"))
        self.threadpool.start(worker)

    def get_temperature(self, progress_callback):
        self.camera.clear_folder()
        self.plot_continuous = False
        # self.set_enable(False)
        N_snap = self.form.spinBox_N_temp.value()
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
        self.ims = temperature.images(dirname)
        # self.set_enable(True)
        # plt.figure()
        # self.ims.plot()
        # plt.show()
        # self.plot_continuous = True
        # return ims

    def take_continuous_pictures_worker(self):
        if self.form.checkBox_plotContinuous.isChecked():
            worker = Worker(self.take_continuous_pictures) # Any other args, kwargs are passed to the run function
            # worker.signals.result.connect(self.print_output)
            # worker.signals.finished.connect(self.thread_complete)
            # worker.signals.progress.connect(self.progress_fn)
            # Execute
            self.threadpool.start(worker)

    def take_continuous_pictures(self, progress_callback):
        # self.plot_continuous = True
        # self.form.checkBox_plotContinuous.setDisabled(True)
        self.print_to_dialogue("Plot Continuous")
        if self.simulation:
            while True:
                for image in self.ims.images:
                    if self.form.checkBox_plotContinuous.isChecked()== False:
                        break
                    time.sleep(0.01)
                    # print(image.std_x)
                    # progress_callback.emit(int(image.std_x))
                    # self.plotData([i for i in range(len(image.line_x))], image.line_x)
                    self.plotData(image)
            return
        # backgroundim = pil.Image.open('background_23-12-2020.png')
        # background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        else:
            self.pgc_experiment.toggle_camera_roll(True)
            self.sigmay = []
            self.sigmax = []
            while self.form.checkBox_plotContinuous.isChecked():
                try:
                    im, _ = self.camera.CaptureImage()
                    if self.form.checkBox_substractBackground.isChecked():
                        imnp = np.asarray(im.convert(mode='L'), dtype=float)-self.background
                    else:
                        imnp = np.asarray(im.convert(mode='L'), dtype=float)
                    imim = temperature.image(imnp)
                    ax, sx, sy = imim.optimizer([500,1300,500,1100])
                    if sx >0:
                        self.sigmay.append(sy)
                        self.sigmax.append(sx)
                        if len(self.sigmax)>30:
                            self.sigmay.pop(0)
                            self.sigmax.pop(0)
                    self.plotData(imim)
                except:
                    print("Failed capturing image")
  
if __name__=="__main__":
    app = QApplication([])
    # ui_dir = "C:\\Users\\Jeremy\\Dropbox\\python_postdoc\\temperature\\GUI_qtdesigner.ui"
    if os.getlogin()=='orelb':
        ui_dir = "C:\\Pycharm\\Expriements\\QM\\temperature\\GUI_qtdesigner.ui"
        simulation = False
    elif os.getlogin()=='Jeremy':
        ui_dir = os.path.join(os.getcwd(), "GUI_qtdesigner.ui")
        simulation = True
    window = experiment_gui(ui_dir, simulation=simulation)
    window.window.show()
    # app.exec_()
    # sys.exit(app.exec_())