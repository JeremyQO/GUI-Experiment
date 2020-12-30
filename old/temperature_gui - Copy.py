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


class experiment_gui (PlotWindow):
    def __init__(self, ui, simulation=True):
        super(experiment_gui, self).__init__()
        Form, Window = uic.loadUiType(ui)
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.form.verticalLayout_mpl.addWidget(self.widgetPlot)
        self.form.tabWidget.tabCloseRequested.connect(self.close_tab)
        self.form.actionPGC.triggered.connect(lambda: print("clicked"))

        # Connects:
        if simulation:
            self.form.pushButton_3.clicked.connect(self.get_continuous_pictures)  
            
        # Experiment initialisation:
        if simulation:
            dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\23-12-2020'
            self.ims = images(dirname, imrange=[0,5])
            
    
    def print_to_dialogue (self, s):
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        self.form.listWidget.addItem(dt_string+" - "+s)
        self.form.listWidget.scrollToBottom()
        
    def close_tab(self,index):
      self.form.tabWidget.removeTab(index)
      print(index)
      
    def get_continuous_pictures(self):
        worker = Worker(self.execute_this_fn) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)
        
    def execute_this_fn(self, progress_callback):
        self.print_to_dialogue("Executing")
        for i in range(1):
            for image in self.ims.images:
                time.sleep(0.01)
                print(image.std_x)
                progress_callback.emit(int(image.std_x))
                # self.plotData([i for i in range(len(image.line_x))], image.line_x)
                self.plotData(image)
              
    def progress_fn(self, s):
        print("Emitted "+str(s)) 
    
    def thread_complete(self):
        print("Thread Complete")
    
    def print_output(self,s):
        print("Output is %.2f"%(s))
  
if __name__=="__main__":
    app = QApplication([])
    ui_dir = "C:\\Users\\Jeremy\\Dropbox\\python_postdoc\\temperature\\better_experiment.ui"
    window = experiment_gui(ui_dir)
    window.window.show()
    # app.exec_()
    # sys.exit(app.exec_())