# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui

To convert *.ui file to *.py:
!C:\\Users\\Jeremy\\anaconda3\\pkgs\\pyqt-impl-5.12.3-py38h885f38d_6\\Library\\bin\\pyuic5.bat -x .\\experiment.ui -o experiment.py
!C:\\Users\\Jeremy\\anaconda3\\pkgs\\pyqt-5.9.2-py38ha925a31_4\\Library\\bin\\pyuic5.bat -x .\gui.ui -o experiment.py
"""

import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import *
import matplotlib
if matplotlib.get_backend()!='Qt5Agg':
    matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool
import time
from datetime import datetime
try:
    import MvCamera
    from old.pgc_macro_Dor import pgc
except:
    pass
import os

from functions.pgc.data_analysis import image, images
import widgets.pgc.dataplot as dataplot
from widgets.worker import Worker 

class Pgc_gui (QWidget):
    def __init__(self, simulation=True):
        super(Pgc_gui, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "gui.ui")
        uic.loadUi(ui, self)
        
        self.widgetPlot = dataplot.PlotWindow()
        self.verticalLayout_mpl.addWidget(self.widgetPlot.widgetPlot)
        self.simulation = simulation
        if __name__=="__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
        # Connects:
        self.pushButton_PGC_Connect.clicked.connect(self.PGC_connect)
        self.checkBox_plotContinuous.clicked.connect(self.take_continuous_pictures_worker)
        self.pushButton_takeBackground.clicked.connect(self.take_new_background_worker)
        self.pushButton_updateSnapTime.clicked.connect(self.update_Snaptime)
        self.pushButton_update_dA.clicked.connect(self.update_dA)
        self.pushButton_update_df.clicked.connect(self.update_df)


    def enable_interface(self,v=True):
        self.frame_5.setEnabled(v)
        self.frame.setEnabled(v)
        self.listWidget_dialogue.setEnabled(v)
        self.widget.setEnabled(v)
        
    def PGC_connect(self):
        # print("Success")
        self.pushButton_PGC_Connect.setDisabled(True)
        self.enable_interface(False)
        if self.simulation:
            dirname = "C:\\Users\\orelb\\Desktop\\MOT_PGC_Fall\\Images" if os.getlogin()=='orelb' else\
                'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\images'
            self.ims = images(dirname)  #, imrange=[0,5])
            self.print_to_dialogue("Images loaded successfully")
            self.enable_interface(True)
            self.pushButton_PGC_Connect.setEnabled(True)
            return

        self.print_to_dialogue("Connecting to OPX...")
        self.pgc_experiment = pgc()
        self.print_to_dialogue("Connected to OPX")
        self.print_to_dialogue("Connecting to Camera...")
        try:
            self.camera = MvCamera.MvCamera()
            self.print_to_dialogue("Connected to camera")
        except Exception as e:
            # self.print_to_dialogue("Camera already connected")
            self.print_to_dialogue(str(e))

        self.enable_interface(True)
        self.pushButton_PGC_Connect.setEnabled(True)

    def update_Snaptime(self):
        v = self.doubleSpinBox_Snap.value()
        if self.simulation:
            self.print_to_dialogue("Updated snaptime to %.2f" % (v))
            return
        self.pgc_experiment.update_snap_time(float(v))
        self.print_to_dialogue("Updated snaptime to %.2f" % (v))
        
    def update_dA(self):
        v = self.doubleSpinBox_dA.value()
        if self.simulation:
            self.print_to_dialogue("Updated dA to %.3f"%(v))
            return
        self.pgc_experiment.update_da(v)
        self.print_to_dialogue("Updated dA to %.3f" % (v))

    def update_df(self):
        v = self.doubleSpinBox_df.value()
        if self.simulation:
            self.print_to_dialogue("Updated df to %.3f"%(v))
            return
        self.pgc_experiment.update_df_pgc(v)
        self.print_to_dialogue("Updated df to %.3f" % (v))

    def take_new_background_worker(self):
        worker = Worker(self.take_new_background)
        worker.signals.finished.connect(lambda: self.print_to_dialogue("New background taken"))
        self.threadpool.start(worker)

    def take_new_background(self, progress_callback):
        # todo: get background. what happens if camera roll is true when clicked ?
        if self.simulation:
            self.checkBox_substractBackground.setEnabled(True)
            return

        self.print_to_dialogue("Snapping Background...")
        self.pgc_experiment.Background()
        backgroundim, _ = self.camera.CaptureImage()
        self.background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        self.checkBox_substractBackground.setEnabled(True)

    def print_to_dialogue (self, s):
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        self.listWidget_dialogue.addItem(dt_string+" - "+s)
        print(dt_string+" - "+s)
        self.listWidget_dialogue.scrollToBottom()

    def take_continuous_pictures_worker(self):
        if self.checkBox_plotContinuous.isChecked():
            worker = Worker(self.take_continuous_pictures) # Any other args, kwargs are passed to the run function
            # worker.signals.result.connect(self.print_output)
            # worker.signals.finished.connect(self.thread_complete)
            # worker.signals.progress.connect(self.progress_fn)
            # Execute
            self.threadpool.start(worker)

    def take_continuous_pictures(self, progress_callback):
        # self.plot_continuous = True
        # self.checkBox_plotContinuous.setDisabled(True)
        self.print_to_dialogue("Plot Continuous")
        if self.simulation:
            for i in range(5):
                for im in self.ims.images:
                    if self.checkBox_plotContinuous.isChecked()== False:
                        break
                    time.sleep(0.01)
                    # progress_callback.emit(int(image.std_x))
                    # self.plotData([i for i in range(len(image.line_x))], image.line_x)
                    self.widgetPlot.plotData(im)
            return
        # backgroundim = pil.Image.open('background_23-12-2020.png')
        # background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        else:
            self.pgc_experiment.toggle_camera_roll(True)
            self.sigmay = []
            self.sigmax = []
            while self.checkBox_plotContinuous.isChecked():
                # try:
                im, _ = self.camera.CaptureImage()
                if self.checkBox_substractBackground.isChecked() and hasattr(self, "background"):
                    imnp = np.asarray(im.convert(mode='L'), dtype=float)-self.background
                else:
                    imnp = np.asarray(im.convert(mode='L'), dtype=float)
                try:
                    imim = image(imnp)
                    ax, sx, sy = imim.optimizing([500,1300,500,1100])
                    if sx >0:
                        self.sigmay.append(sy)
                        self.sigmax.append(sx)
                        if len(self.sigmax)>30:
                            self.sigmay.pop(0)
                            self.sigmax.pop(0)
                    self.widgetPlot.plotData(imim)
                except RuntimeError as e:
                    print(e)

                # except Exception as e:
                #     print("Failed capturing image")
                #     print(e)
  
if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Pgc_gui(simulation=simulation)
    window.show()
    app.exec_()
    # import sys
    # sys.exit(app.exec_())