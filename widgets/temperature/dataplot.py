# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 16:52:30 2020

@author: Jeremy
"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
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
        
        # ax1 = plt.subplot2grid((2, 2), (1, 1),  colspan=2, rowspan=2)
        # ax2 = plt.subplot2grid((2,2),(0,1), colspan=2, rowspan=1)
        # ax3 = plt.subplot2grid((2,2),(1,0), colspan=1, rowspan=2)
        # ax4 = plt.subplot2grid((2, 2), (0,0),  colspan=1, rowspan=1)
        ax1 = plt.subplot2grid((2, 2), (1, 1),  colspan=1, rowspan=1)
        ax2 = plt.subplot2grid((2,2),(0,1), colspan=1, rowspan=1)
        ax3 = plt.subplot2grid((2,2),(1,0), colspan=1, rowspan=1)
        ax4 = plt.subplot2grid((2, 2), (0,0),  colspan=1, rowspan=1)
        plt.tight_layout()
      
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)


        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        self.widgetPlot = widget

    def plotData(self, ims):
        self.figure.clear()
        ims.plot()
        plt.tight_layout()
        self.canvas.draw()
