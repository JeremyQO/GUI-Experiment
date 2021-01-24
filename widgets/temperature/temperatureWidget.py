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
    from OPXcontrol.pgc_macro_with_OD import pgc
except:
    pass
import os

from functions.temperature.data_analysis import images, image
from widgets.worker import Worker

from widgets.quantumWidget import QuantumWidget


class Temperature_gui (QuantumWidget):
    def __init__(self, Parent=None, ui=None, simulation=True):
        if Parent is not None:
            self.Parent = Parent
        ui = os.path.join(os.path.dirname(__file__), "gui.ui") if ui is None else ui
        super(Temperature_gui, self).__init__(ui, simulation)

        self.OPX = None
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
        
        if os.getlogin() == 'orelb':
            dirname = 'C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images'
            self.lineEdit_Folder.setText(dirname)
            self.pushButton_get_temperature_fromFolder.setEnabled(True)
            self.picturesDirName = dirname
        else:
            dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\23-12-2020'
            self.lineEdit_Folder.setText(dirname)
            self.pushButton_get_temperature_fromFolder.setEnabled(True)
            self.picturesDirName = dirname
    
    def updateCal(self):
        calibration =  self.LineEdit_CalPixMM.text()
        try:
            self.pixelCal = float(calibration)
            self.print_to_dialogue("Pixels per mm: %.1f"%(float(calibration)))
        except ValueError:
            self.alert_box("Calibration must be float")

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
        try:
            if hasattr(self, 'Parent'):
                if self.Parent.OPX is not None:
                    self.OPX = self.Parent.OPX
                    self.print_to_dialogue("Grabbed OPX from parent")
                else:
                    self.OPX = pgc()
                    self.Parent.OPX = self.OPX
                    self.print_to_dialogue("Connected to OPX")
            else:
                self.OPX = pgc()
                self.print_to_dialogue("Connected to OPX")
        except NameError:
            self.print_to_dialogue("Couldn't connect to OPX")
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

        dirname = 'C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images'
        self.plot_continuous = False
        # self.set_enable(False)
        self.widgetPlot.sigmay = []
        self.widgetPlot.sigmax = []
        
        now = datetime.now()
        today = date.today()
        imagesdirname = today.strftime("%b-%d-%Y_") + now.strftime("%H-%M-%S")
        imagesdir = os.path.join(dirname, imagesdirname)
        if not os.path.isdir(imagesdir):
            os.mkdir(imagesdir)
            
        N_snap = self.spinBox_N_temp.value()
        self.OPX.measure_temperature(N_snap)
        for i in range(1, N_snap + 1):
            self.print_to_dialogue("Snap at %.2f ms" % (i))
            im, _ = self.camera.CaptureImage()
            imnp = np.asarray(im.convert(mode='L'), dtype=float)
            try:
                imim = image(imnp)
                ax, sx, sy = imim.optimizing([500, 1300, 500, 1100])
                self.widgetPlot.sigmay.append(sy)
                self.widgetPlot.sigmax.append(sx)
                self.widgetPlot.plotImages(imim)
                now = datetime.now()
                imname = imagesdir + "\\" +now.strftime("%H-%M-%S_")
                imname+= 't=' + "%.2f"%(i) + '.png'
                im.save(imname, "PNG")
                # self.camera.SaveImageT(im, "%.2f" % (i))
                progress_callback.emit(i * 100 / N_snap)
            except RuntimeError:
                self.print_to_dialogue("Couldn't fit... stopping")
                # self.alert_box("couldn't fit")
                break

        print("Taking background")
        self.OPX.Background()
        backgroundim, _ = self.camera.CaptureImage()
        now = datetime.now()
        imname = imagesdir + "\\" +now.strftime("%H-%M-%S_")
        imname+= "background" + '.png'
        backgroundim.save(imname, "PNG")
        self.background = np.asarray(backgroundim.convert(mode='L'), dtype=float)
        # self.camera.SaveImageT(backgroundim, 0, background=True)

        try:
            self.ims = images(imagesdir)
            self.widgetPlot.plotData(self.ims)
        except RuntimeError :
            self.print_to_dialogue("Optimal parameters not found: Number of calls to function has reached maxfev = 800.")

    @pyqtSlot()
    def returnPressedSlot(self):
        dirname =  self.lineEdit_Folder.text()
        print(dirname)
        print(os.path.isdir(dirname))
        if os.path.isdir(dirname):
            self.picturesDirName = dirname
        else:
            self.alert_box("Invalid folder name!\n" + dirname)

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
            try:
                self.ims = images(dirname)
                self.ims.pixelCal = self.pixelCal
                self.widgetPlot.plotData(self.ims)
                self.print_to_dialogue("Tx = %.2f uK, Ty = %.2f uK" % (self.ims.Tx * 1e6, self.ims.Ty * 1e6))
            except IndexError :
                self.alert_box("Directory does not contain any images")
            except IndexError:
                self.alert_box("No background image found")
            except RuntimeError:
                self.alert_box("Optimal parameters not found: Number of calls to function has reached maxfev = 800.")


if __name__=="__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = Temperature_gui(simulation=simulation)
    window.show()
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())