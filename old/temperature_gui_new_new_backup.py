# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui
* Make fucntion class inherit the main window class that contains the *.ui

To convert *.ui file to *.py:
!C:\\Users\\Jeremy\\anaconda3\\pkgs\\pyqt-impl-5.12.3-py38h885f38d_6\\Library\\bin\\pyuic5.bat -x .\\experiment.ui -o experiment.py

"""

from temperature_for_gui import images
import numpy as np
import time
# import matplotlib.pylab as plt
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout
import sys
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSlot, QObject, pyqtSignal, QTimer
import traceback, sys
import random


class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        # self.setLayout(layout)
        self.layoutPlot = layout

    def plot(self):
        ''' plot some random stuff '''
        # random data
        data = [random.random() for i in range(10)]

        # instead of ax.hold(False)
        self.figure.clear()

        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        # ax.hold(False) # deprecated, see above

        # plot data
        ax.plot(data, '*-')

        # refresh canvas
        self.canvas.draw()

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress
        


    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class MplCanvas(FigureCanvas):

    def __init__(self, axis = None, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        if axis is None:
            self.axes = fig.add_subplot(111)
            self.axes.set_title("Title $\\mu$")
        super().__init__(fig)

class experiment_gui (PlotWindow):
    def __init__(self, ui):
        super(PlotWindow, self).__init__()
        Form, Window = uic.loadUiType(ui)
        app = QApplication([])
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.form.verticalLayout_mpl.addWidget(self.layoutPlot)
        # self.initializePlot()
        self.form.pushButton_4.clicked.connect(self.plot)     
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # self.form.pushButton_3.clicked.connect(self.exe_infinite_plot)
        self.form.pushButton_3.clicked.connect(self.prin)
        self.window.show()
    
    def StaticPlot(self, x,y):
        sc = MplCanvas(parent=self.window, width=12.4, height=8.0, dpi=100)

        sc.axes.plot(x,y) 
        sc.setObjectName("tempplotsc")

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(sc, self.window)
        
        # layout = self.form.verticalLayout_mpl
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)
        layout.setObjectName("tempplotlayout")

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName("tempplotwidget")
        if hasattr(self, 'temperatureplot'):
            self.form.verticalLayout_mpl.removeWidget(self.temperatureplot)
        self.temperatureplot = widget
        self.form.verticalLayout_mpl.addWidget(widget)
        
    def prin(self):
        t = time.time()
        print(t)
        # data = [15,2,3,1]
        x = np.linspace(0,4*np.pi,100)
        y = np.sin(x+t)
        self.plot(x,y)     
        
        # self.form.verticalLayout_mpl.addWidget(self.temperatureplot)
        
        
        
    
    def infinite_plot(self, progress_callback):

        # data = [15,2,3,1]
        x = np.linspace(0,4*np.pi,100)  
        
        # self.form.verticalLayout_mpl.addWidget(self.temperatureplot)
        
        for i in range(10):
            time.sleep(0.5)
            t = time.time()
            print(t)
            y = np.sin(x+t)
            widget = self.StaticPlot(x,y) 
            if hasattr(self, 'temperatureplot'):
                self.form.verticalLayout_mpl.removeWidget(self.temperatureplot)
            self.temperatureplot = widget
            self.form.verticalLayout_mpl.addWidget(widget)
    
    def exe_infinite_plot(self):
        worker = Worker(self.infinite_plot)
        self.threadpool.start(worker)
    
if __name__=="__main__":
    app = QApplication([])
    ui_dir = "C:\\Users\\Jeremy\\Dropbox\\python_postdoc\\temperature\\experiment.ui"
    window = experiment_gui(ui_dir)
    
    # app.exec_()
    # sys.exit(app.exec_())