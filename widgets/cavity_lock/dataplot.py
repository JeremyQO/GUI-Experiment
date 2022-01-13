# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 16:52:30 2020

@author: Jeremy
"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout
import matplotlib
if matplotlib.get_backend()!='Qt5Agg':
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
    
    def plot(self, x, y=None):
        self.figure.clear()
        if y is None:
            plt.plot(x)
        else:
            plt.plot(x, y)
        plt.tight_layout()
        self.canvas.draw()

    def plot_OD(self, x, y1, y2, cursors, autoscale=True):
        # xmin, xmax, ymin, ymax = plt.axis()
        ymin, ymax = plt.ylim()
        xmin, xmax = plt.xlim()
        self.figure.clear()
        plt.plot(x, y1, label="Depump")
        plt.plot(x, y2, label="OD")
        if not autoscale:
            plt.ylim(ymin, ymax)
            plt.xlim(xmin, xmax)
        for curs in cursors:
            plt.axvline(curs, c='r')
        plt.ylabel('Power (a.u.)')
        plt.xlabel('Time ($\\mu s$)')
        plt.legend()
        plt.tight_layout()
        self.canvas.draw()
    
    def plotData(self, ims):
        self.figure.clear()
        ims.plot()
        plt.tight_layout()
        self.canvas.draw()

    def plot_traces(self, data, time, truthiness, labels, cursors, autoscale=True, sensitivity=None, 
                    nathistory=None, boxText="", xaxis_history=[]):
        try:
            y1min, y1max = self.ax1.get_ylim()
            x1min, x1max = self.ax1.get_xlim()
            y2min, y2max = self.ax2.get_ylim()
        except AttributeError:
            autoscale = True
        self.figure.clear()
        self.ax1 = plt.subplot2grid((3, 1), (0, 0), colspan=1, rowspan=2)
        self.ax3 = plt.subplot2grid((3, 1), (2, 0), colspan=1, rowspan=1)
        colors = ['b', 'g', 'r', 'c', 'k', 'm', 'y', 'darkorange']
        for i, el in enumerate(data):
            if truthiness[i]:
                self.ax1.plot(time, el, color=colors[i], label=labels[i])

        if not autoscale:
            self.ax1.set_ylim(y1min, y1max)
            self.ax1.set_xlim(x1min, x1max)
            self.ax2.set_ylim(y2min, y2max)
        for curs in cursors:
            self.ax1.axvline(curs, c='r', linestyle='--', alpha=0.4)

        if sensitivity is not None:
            self.ax2 = self.ax1.twinx()
            self.ax2.set_ylabel('Power (uW)')
            y1min, y1max = self.ax1.get_ylim()
            self.ax2.set_ylim(y1min/sensitivity*1e6, y1max/sensitivity*1e6)

        if nathistory is not None:
            if xaxis_history==[]:
                self.ax3.plot([float(el/1e6) for el in nathistory])
                self.ax3.plot([float(el/1e6) for el in nathistory], 'or')
                self.ax3.set_ylabel('$N_{\mathrm{at}}$ (milions)')
            else:
                self.ax3.plot(xaxis_history[:len(nathistory)], nathistory)
                self.ax3.plot(xaxis_history[:len(nathistory)], nathistory, 'or')
                self.ax3.set_ylabel('Transmission')

        self.ax1.set_xlabel('Time ($\mu$s)')
        self.ax1.set_ylabel('Voltage (V)')
        self.ax1.legend()
        # plt.legend(loc='upper right')
        plt.tight_layout()
        # refresh canvas
        self.canvas.draw()

    def plotDataPGC(self,im, axSigma = None, aoe=None):

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
        ax1.imshow(m, interpolation='none', cmap='rainbow')
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

    def plotImages(self, im, axSigma = None, aoe=None):
        # print(self.xdata)
        self.figure.clear()

        # create an axis
        ax1 = plt.subplot2grid((2, 2), (1, 1), colspan=2, rowspan=2)
        ax2 = plt.subplot2grid((2, 2), (0, 1), colspan=2, rowspan=1)
        ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=1, rowspan=2)
        ax4 = plt.subplot2grid((2, 2), (0, 0), colspan=1, rowspan=1)

        # discards the old graph
        # ax.hold(False) # deprecated, see above

        # plot data
        if aoe is not None:
            xa, xb, ya, yb = aoe
            m = im.npimage[ya:yb, xa:xb]
            ax1.axvline(x=im.c_x - xa, color='red')
            ax1.axhline(y=im.c_y - ya, color='red')
        else:
            m = im.npimage
            ax1.axvline(x=im.c_x, color='red')
            ax1.axhline(y=im.c_y, color='red')
        ax1.imshow(m, interpolation='none')
        ax2.plot(im.xaxis, im.line_x, label='x axis')
        ax2.plot(im.xaxis, gaussian(im.xaxis, *im.popt_x), label='STD=%.0f' % (im.std_x))
        ax2.legend()
        ax3.plot(im.yaxis, im.line_y, label='y axis')
        ax3.plot(im.yaxis, gaussian(im.yaxis, *im.popt_y), label='STD=%.0f' % (im.std_y))
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
        

