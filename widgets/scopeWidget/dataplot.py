# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 16:52:30 2020

@author: Jeremy
"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout
import matplotlib
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np


def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-((x - mean) ** 2 / 2 / stddev ** 2))


class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)

        plt.ion()
        self.figure = plt.figure(1)
        self.ax1 = self.figure.add_subplot(111)
        self.arrows = [None] * 2 #len(kwargs['mark_peak'])  # Create placeholder for 2 arrows
        self.markedPeaks = None
        self.scatter = None # Placeholder
        self.annotations = []
        self.annotations = None
        self.textBox = None
        self.lines = []
        for i in range(2): # in principle, hold 4 places for lines. With good coding, this is not neccessary
            line1, = self.ax1.plot([1], [1], 'r-')  # Returns a tuple of line objects, thus the comma
            self.lines.append(line1)

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)


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

    def plot_Scope(self, x_data,y_data, autoscale = False, redraw = False, **kwargs):
        if not redraw:  # meanning - merely update data, without redrawing all.
            for i, line in enumerate(y_data):
                self.lines[i].set_ydata(y_data[i])
            if autoscale:
                miny, maxy = min(y_data[0]), max(y_data[0])
                headroom = np.abs(maxy - miny) * 0.05 # leaving some room atop and below data in graph
                self.ax1.set_ylim(min(y_data[0]) - headroom, max(y_data[0]) + headroom)
                ticks = np.linspace(miny, maxy, 10)
                self.ax1.set_yticks(ticks)
                self.ax1.set_yticklabels(['{:5.3f}'.format(t) for t in ticks])  # 10 divisions for autoscale
            if 'aux_plotting_func' in kwargs:
                kwargs['aux_plotting_func'](**kwargs)  # This is a general way of calling this function
            if 'mark_peak' in kwargs and kwargs['mark_peak'] is not None:
                self.markPeaks(kwargs['mark_peak'])
                for i, pk in enumerate(kwargs['mark_peak']):
                    if self.arrows[i] is None:
                        self.arrows[i] = self.annotateWithArrow(pk[0], pk[1])   # create new arrow
                    self.arrows[i].xy = (pk[0],pk[1])                                # update arrow location
            if 'text_box' in kwargs and kwargs['text_box'] is not None:
                if self.textBox is None: self.addTextBox(textstr=kwargs['text_box'])
                self.textBox.set_text(str(kwargs['text_box']))
            return

        print('Redrawing all')
        self.arrows = [None] * 2 # reset arrow
        self.textBox = None # reset textbox
        if 'labels' not in kwargs:
            kwargs['legend'] = False
            kwargs['labels'] = [''] * 10 # to prevent glitches

        self.ax1 = None
        self.figure.clear()
        self.scatter = None
        self.markedPeaks = None
        self.ax1 = self.figure.add_subplot(111)

        for i, el in enumerate(np.array(y_data)):
            line1, = self.ax1.plot(x_data, el, label=kwargs['labels'][i])  # Returns a tuple of line objects, thus the comma
            self.lines[i] = line1

        # ------ legend ----------------
        if 'legend' in kwargs and kwargs['legend'] or 'legend' not in kwargs: # by default, legend on
            self.ax1.legend(loc = 'lower left') # defualt
            if 'legend_loc' in kwargs: self.ax1.legend(loc = kwargs['legend_loc'])

        # --------  Secondary scale ---------
        if 'secondary_x_axis_func' in kwargs and kwargs['secondary_x_axis_func']:
            sec_ax = self.ax1.secondary_xaxis('top',xlabel=kwargs['secondary_x_axis_label'], functions = kwargs['secondary_x_axis_func'])

        # ------ grid ----------------
        if 'grid' in kwargs and kwargs['grid'] or 'grid' not in kwargs: # by default, grid on
            if 'x_ticks' in kwargs:
                self.ax1.set_xticks(kwargs['x_ticks'])
            if 'y_ticks' in kwargs:
                self.ax1.set_yticks(kwargs['y_ticks'])
            self.ax1.grid()

        # ------ limits ----------------
        if autoscale:
            self.ax1.set_ylim(min(y_data[0]), max(y_data[0]) * 1.1)
        elif 'y_ticks' in kwargs:
            self.ax1.set_ylim(kwargs['y_ticks'][0], kwargs['y_ticks'][-1])
        self.ax1.set_xlim(x_data[0], x_data[-1])

        self.ax1.set_ylabel('Voltage [V]')
        self.ax1.set_xlabel('Time [ms]')
        if 'aux_plotting_func' in kwargs:
            kwargs['aux_plotting_func'](**kwargs) # This is a general way of calling this function
        plt.tight_layout()

        self.canvas.draw()

    def plot_Scatter(self, **kwargs):
        # first - check we have what we need
        if 'scatter_x_data' and 'scatter_y_data' in kwargs and kwargs['scatter_x_data'] != [] and kwargs['scatter_y_data'] != []:
            x_data, y_data = kwargs['scatter_x_data'], kwargs['scatter_y_data']

            #------- First, handle scatter -------
            # if scatter don't exist - scatter for the first time
            if not self.scatter:# or  (self.scatter is not None and len() != len(x_data) ):
                # draw scatter + define style
                self.scatter = self.ax1.scatter(x_data, y_data, marker="x", color="b")
            else:  # merely update location
                self.scatter.set_offsets(np.c_[x_data, y_data])  # this seems to work.

            # --------------- annotate! (currently not in use, though should work) ----------
            if 'scatter_tags' in kwargs and  kwargs['scatter_tags'] != []:
                # if annotations don't exist (and there are enough tags) - annontate for the first time
                if (self.annotations is None or self.annotations == [])and len(kwargs['scatter_tags']) == len(x_data):
                    # draw scatter + define style
                    self.annotations = []
                    for i, x in enumerate(x_data):
                        # annotate scatter + define style
                        self.annotations.append(self.ax1.annotate(kwargs['scatter_tags'][i], xy = (x, y_data[i]), weight='bold' ))
                # If they exist - update location
                else:
                    if self.annotations:
                        for i, s in enumerate(self.annotations): s.set_position((x_data[i], y_data[i]))
            # if annotation exists, but of different length, remove previous ones.
            elif self.annotations is not None and len(self.annotations) != len(x_data):
                for ann in self.annotations:
                    ann.remove()
                self.annotations = []


    def markPeaks(self, peaksCoordinates):
        x_data, y_data = zip(*peaksCoordinates) # turns [(x0,y0),(x1,y1)] into [(x0,x1),(y0,y1)]
        # if scatter don't exist - scatter for the first time
        if not self.markedPeaks:
            # draw scatter + define style
            self.markedPeaks = self.ax1.scatter(x_data, y_data, marker="o", color="r")
        else:  # merely update location
            self.markedPeaks.set_offsets(np.c_[x_data, y_data])  # this seems to work.

    def annotateWithArrow(self, x,y):
        return(self.ax1.annotate('', xy=(x, y),  xycoords='data',
            xytext=(0.8, 0.95), textcoords='axes fraction',
            arrowprops=dict(facecolor='black', shrink=0.05),
            horizontalalignment='right', verticalalignment='top'))
    def addTextBox(self, textstr):
        props = dict(boxstyle='round', facecolor='grey', alpha=0.1)
        self.textBox = self.ax1.text(0.05, 0.95, textstr, transform=self.ax1.transAxes, fontsize=14,
        verticalalignment='top', bbox=props)
