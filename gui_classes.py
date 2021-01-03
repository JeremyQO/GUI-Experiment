# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 16:52:30 2020

@author: Jeremy
"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout
import sys
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal
import traceback
import random
import numpy as np

def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-((x - mean)**2 / 2 / stddev**2))



class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)

        # a figure instance to plot on
        plt.ioff()
        self.figure = plt.figure(1)

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        
        ax1 = plt.subplot2grid((2, 2), (1, 1),  colspan=2, rowspan=2)
        ax2 = plt.subplot2grid((2,2),(0,1), colspan=2, rowspan=1)
        ax3 = plt.subplot2grid((2,2),(1,0), colspan=1, rowspan=2)
        ax4 = plt.subplot2grid((2, 2), (0,0),  colspan=1, rowspan=1)
        plt.tight_layout()
      
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        # self.canvas.draw()
        # Just some button connected to `plot` method
        # self.button = QPushButton('Plot')
        # self.button.clicked.connect(self.plot)

        # set the layout
        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        # layout.addWidget(self.button)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        # widget.setObjectName("mpl_widget_plot")
        # self.setLayout(layout) # is what was here in example
        self.widgetPlot = widget

        # For temperature tab:
        # self.figure_temp = plt.figure(2)
        # self.canvas_temp = FigureCanvas(self.figure_temp)
        # ax1t = plt.subplot2grid((2, 2), (1, 1),  colspan=2, rowspan=2)
        # ax2t = plt.subplot2grid((2,2),(0,1), colspan=2, rowspan=1)
        # ax3t = plt.subplot2grid((2,2),(1,0), colspan=1, rowspan=2)
        # ax4t = plt.subplot2grid((2, 2), (0,0),  colspan=1, rowspan=1)
        # plt.tight_layout()
        # self.toolbar_temp = NavigationToolbar(self.canvas_temp, self)
        # layout_temp = QVBoxLayout()
        # layout_temp.addWidget(self.toolbar_temp)
        # layout_temp.addWidget(self.canvas_temp)
        # # layout.addWidget(self.button)
        # widget_temp = QtWidgets.QWidget()
        # widget_temp.setLayout(layout_temp)
        # widget_temp.setContentsMargins(0, 0, 0, 0)
        # # widget.setObjectName("mpl_widget_plot")
        # # self.setLayout(layout) # is what was here in example
        # self.widgetPlot_temp = widget_temp
    
    def plotData(self,im, axSigma = None, aoe=None):

        # print(self.xdata)
        self.figure.clear()

        # create an axis
        ax1 = plt.subplot2grid((2, 2), (1, 1),  colspan=2, rowspan=2)
        ax2 = plt.subplot2grid((2,2),(0,1), colspan=2, rowspan=1)
        ax3 = plt.subplot2grid((2,2),(1,0), colspan=1, rowspan=2)
        ax4 = plt.subplot2grid((2, 2), (0,0),  colspan=1, rowspan=1)

        # discards the old graph
        # ax.hold(False) # deprecated, see above

        # plot data
        if aoe is not None:
            xa, xb, ya, yb = aoe
            m = im.npimage[ya:yb, xa:xb]
            ax1.axvline(x=im.c_x-xa, color='red')
            ax1.axhline(y=im.c_y-ya, color='red')
        else:
            m = im.npimage
            ax1.axvline(x=im.c_x, color='red')
            ax1.axhline(y=im.c_y, color='red')
        ax1.imshow(m, interpolation='none')   
        ax2.plot(im.xaxis, im.line_x, label='x axis')
        ax2.plot(im.xaxis, gaussian(im.xaxis, *im.popt_x),label='STD=%.0f'%(im.std_x))
        ax2.legend()
        ax3.plot(im.yaxis, im.line_y,label='y axis')
        ax3.plot(im.yaxis, gaussian(im.yaxis, *im.popt_y),label='STD=%.0f'%(im.std_y))
        ax3.legend()
        
        # ax4.text(0.2,0.6, '$\sigma_x=%.0f$'%(im.std_x), fontsize=55,  color='black')
        # ax4.text(0.2,0.2, '$\sigma_y=%.0f$'%(im.std_y), fontsize=55,  color='black')
        if hasattr(self, 'sigmax'):
            ax4.plot(self.sigmax, '-o', label="$\sigma_x$")
            ax4.plot(self.sigmay, '-o', label="$\sigma_y$")
            ax4.legend(loc="upper right")
        plt.tight_layout()

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