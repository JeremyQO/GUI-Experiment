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
from PyQt5.QtWidgets import QApplication
import matplotlib
if matplotlib.get_backend()!='Qt5Agg':
    matplotlib.use('Qt5Agg')
from PyQt5.QtCore import QThreadPool
import time
try:
    from functions.pgc import MvCamera
    # from OPXcontrol.OPX_control_New_v1 import OPX
    from mvIMPACT import acquire
except:
    pass
import os

from functions.pgc.data_analysis import image, images
from widgets.worker import Worker 

from widgets.quantumWidget import QuantumWidget


class Pgc_gui (QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        super(Pgc_gui, self).__init__(ui, simulation)

        if __name__=="__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
        # Connects:
        self.pushButton_PGC_Connect.clicked.connect(self.PGC_connect_worker)
        self.checkBox_plotContinuous.clicked.connect(self.take_continuous_pictures_worker)
        self.pushButton_takeBackground.clicked.connect(self.take_new_background_worker)
        # self.pushButton_updateSnapTime.clicked.connect(self.update_Snaptime)
        # self.pushButton_update_dA.clicked.connect(self.update_dA)
        # self.pushButton_update_df.clicked.connect(self.update_df)
        
        self.checkBox_iPython.clicked.connect(self.showHideConsole)
        self.checkBox_parameters.clicked.connect(self.showHideParametersWindow)

        self.enable_interface(False)
    
    def enable_interface(self,v=True):
        # self.frame_5.setEnabled(v)
        self.widget.setEnabled(v)
        self.checkBox_plotContinuous.setEnabled(v)
        self.pushButton_takeBackground.setEnabled(v)
        self.widget_2.setEnabled(v)
        self.checkBox_parameters.setEnabled(v)
        self.frame_parameters.setEnabled(v)

    def PGC_connect_worker(self):
        worker = Worker(self.PGC_connect)
        self.pushButton_PGC_Connect.setDisabled(True)
        worker.signals.finished.connect(lambda: self.pushButton_PGC_Connect.setEnabled(True))
        # worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def PGC_connect(self, progress_callback):
        self.enable_interface(False)
        if self.simulation:
            dirname = "C:\\Users\\orelb\\Desktop\\MOT_PGC_Fall\\Images" if os.getlogin()=='orelb' else\
                'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\images'
            self.ims = images(dirname)  #, imrange=[0,5])
            self.print_to_dialogue("Images loaded successfully")
            self.enable_interface(True)
            self.pushButton_PGC_Connect.setEnabled(True)
            return

        self.print_to_dialogue("Connecting to Camera...")
        try:
            self.camera = MvCamera.MvCamera()
            self.print_to_dialogue("connected to camera")
        except acquire.EDeviceManager:
            self.print_to_dialogue("Camera was already connected")

        self.connectOPX()

        self.enable_interface(True)
        self.pushButton_PGC_Connect.setEnabled(True)

    # def update_Snaptime(self):
    #     v = self.doubleSpinBox_Snap.value()
    #     if self.simulation:
    #         self.print_to_dialogue("Updated snaptime to %.2f" % (v))
    #         return
    #     self.OPX.update_snap_time(float(v))
    #     self.print_to_dialogue("Updated snaptime to %.2f" % (v))
        
    # def update_dA(self):
    #     v = self.doubleSpinBox_dA.value()
    #     if self.simulation:
    #         self.print_to_dialogue("Updated dA to %.3f"%(v))
    #         return
    #     self.OPX.update_lin_pgc_final_amplitude(v)
    #     self.print_to_dialogue("Updated dA to %.3f" % (v))

    # def update_df(self):
    #     v = self.doubleSpinBox_df.value()
    #     if self.simulation:
    #         self.print_to_dialogue("Updated df to %.3f"%(v))
    #         return
    #     self.OPX.update_pgc_final_freq(v)
    #     self.print_to_dialogue("Updated df to %.3f" % (v))

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
        # self.OPX.update_snap_time(10)
        # self.OPX.Imaging_switch(True)
        # self.OPX.update_parameters()
        backgroundim, _ = self.camera.CaptureImage()
        # time.sleep(5)
        self.background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        v = self.frame_parameters.doubleSpinBox_FinalPGCFreq.value()
        self.OPX.update_snap_time(float(v))
        self.OPX.update_parameters()
        self.checkBox_substractBackground.setEnabled(True)

    def take_continuous_pictures_worker(self):
        if self.checkBox_plotContinuous.isChecked():
            worker = Worker(self.take_continuous_pictures) # Any other args, kwargs are passed to the run function
            # worker.signals.result.connect(self.print_output)
            worker.signals.finished.connect(self.thread_complete)
            # worker.signals.progress.connect(self.progress_fn)
            # Execute
            self.threadpool.start(worker)
        # elif not self.simulation:
        #     self.OPX.Imaging_switch(False)
        #     self.OPX.update_parameters()

    def thread_complete(self):
        self.print_to_dialogue("Acquisition stopped")

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
                    self.widgetPlot.plotDataPGC(im)
            return
        # backgroundim = pil.Image.open('background_23-12-2020.png')
        # background = np.asarray(backgroundim.convert(mode='L'), dtype=float)

        # self.OPX.Imaging_switch(True)
        # self.OPX.update_parameters()
        self.widgetPlot.sigmay = []
        self.widgetPlot.sigmax = []
        while self.checkBox_plotContinuous.isChecked():
            # try:
            im, _ = self.camera.CaptureImage(TimeOut_ms=1000000000)
            if self.checkBox_substractBackground.isChecked() and hasattr(self, "background"):
                imnp = np.asarray(im.convert(mode='L'), dtype=float)-self.background
            else:
                imnp = np.asarray(im.convert(mode='L'), dtype=float)

            imim = image(imnp)
            ax, sx, sy = imim.optimizing([500,1300,500,1100])
            if sx >0:
                self.widgetPlot.sigmay.append(sy)
                self.widgetPlot.sigmax.append(sx)
                if len(self.widgetPlot.sigmax)>30:
                    self.widgetPlot.sigmay.pop(0)
                    self.widgetPlot.sigmax.pop(0)
            self.widgetPlot.plotDataPGC(imim)

                    

if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Pgc_gui(simulation=simulation)
    window.show()
    app.exec_()
    # import sys
    # sys.exit(app.exec_())