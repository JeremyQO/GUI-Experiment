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
        self.axes = []
        self.axes.append(self.figure.add_subplot(111))
        self.arrows = [None] * 2 #len(kwargs['mark_peak'])  # Create placeholder for 2 arrows
        self.markedPeaks = None
        self.scatter = None # Placeholder
        self.annotations = []
        self.annotations = None
        self.textBox = None
        self.lines = []

        for i in range(1,2):
            self.axes.append(self.axes[0].twinx())
        for i in range(2): # in principle, hold 4 places for lines. With good coding, this is not neccessary
            line1, = self.axes[i].plot([1], [1], 'r-')  # Returns a tuple of line objects, thus the comma
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
        if not redraw:  # meaning - merely update data, without redrawing all.
            for i, line in enumerate(y_data):
                self.lines[i].set_ydata(y_data[i])
                if autoscale:
                    miny, maxy = min(y_data[i]), max(y_data[i])
                    headroom = np.abs(maxy - miny) * 0.05 # leaving some room atop and below data in graph
                    self.axes[i].set_ylim(min(y_data[i]) - headroom, max(y_data[i]) + headroom)
                    ticks = np.linspace(miny, maxy, 10)
                    self.axes[i].set_yticks(ticks)
                    self.axes[i].set_yticklabels(['{:5.3f}'.format(t) for t in ticks])  # 10 divisions for autoscale
            if 'aux_plotting_func' in kwargs:
                kwargs['aux_plotting_func'](redraw = redraw, **kwargs)  # This is a general way of calling this function
            if 'mark_peak' in kwargs and kwargs['mark_peak'] is not None:
                self.markPeaks(kwargs['mark_peak'])
                for i, pk in enumerate(kwargs['mark_peak']):
                    if self.arrows[i] is None:
                        self.arrows[i] = self.annotateWithArrow(pk[0], pk[1])   # create new arrow
                    self.arrows[i].xy = (pk[0],pk[1])                           # update arrow location
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

        self.figure.clear()
        self.scatter = None
        self.markedPeaks = None
        for ax in self.axes:
            ax = None
        self.axes[0] = self.figure.add_subplot(111)

        for i in range(1,2):
            self.axes[i] = self.axes[0].twinx()

        for i, el in enumerate(np.array(y_data)):
            line1, = self.axes[i].plot(x_data, el, label=kwargs['labels'][i])  # Returns a tuple of line objects, thus the comma
            self.lines[i] = line1

        # ------ legend ----------------
        if 'legend' in kwargs and kwargs['legend'] or 'legend' not in kwargs: # by default, legend on
            self.axes[0].legend(loc = 'upper right') # defualt
            if 'legend_loc' in kwargs: self.axes[0].legend(loc = kwargs['legend_loc'])

        # --------  Secondary scale ---------
        if 'secondary_x_axis_func' in kwargs and kwargs['secondary_x_axis_func']:
            sec_ax = self.axes[0].secondary_xaxis('top',xlabel=kwargs['secondary_x_axis_label'], functions = kwargs['secondary_x_axis_func'])

        # ------ grid ----------------
        if 'grid' in kwargs and kwargs['grid'] or 'grid' not in kwargs: # by default, grid on
            if 'x_ticks' in kwargs:
                self.axes[0].set_xticks(kwargs['x_ticks'])
            if 'y_ticks' in kwargs:
                y_ticks = kwargs['y_ticks']
                for i, ticks in y_ticks:
                    self.axes[i].set_yticks(ticks)
            self.axes[0].grid()

        # ------ limits ----------------
        for i, ax in enumerate(self.axes):
            if autoscale:
                self.axes[i].set_ylim(min(y_data[i][0]), max(y_data[i][0]) * 1.1)
            elif 'y_ticks' in kwargs:
                self.axes[i].set_ylim(kwargs['y_ticks'][i][0], kwargs['y_ticks'][i][-1])
            self.axes[0].set_xlim(x_data[0], x_data[-1])

        self.axes[0].set_ylabel('Voltage [V]')
        self.axes[0].set_xlabel('Time [ms]')
        if 'aux_plotting_func' in kwargs:
            kwargs['aux_plotting_func'](redraw = redraw, **kwargs) # This is a general way of calling this function
        plt.tight_layout()

        self.canvas.draw()

    def plot_Scatter(self,ax_index = 0, **kwargs):
        # first - check we have what we need
        if 'scatter_x_data' and 'scatter_y_data' in kwargs and kwargs['scatter_x_data'] != [] and kwargs['scatter_y_data'] != []:
            x_data, y_data = kwargs['scatter_x_data'], kwargs['scatter_y_data']

            #------- First, handle scatter -------
            # if scatter don't exist - scatter for the first time
            if not self.scatter:# or  (self.scatter is not None and len() != len(x_data) ):
                # draw scatter + define style
                self.scatter = self.axes[ax_index].scatter(x_data, y_data, marker="x", color="b")
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
                        self.annotations.append(self.axes[ax_index].annotate(kwargs['scatter_tags'][i], xy = (x, y_data[i]), weight='bold' ))
                # If they exist - update location
                else:
                    if self.annotations:
                        for i, s in enumerate(self.annotations): s.set_position((x_data[i], y_data[i]))
            # if annotation exists, but of different length, remove previous ones.
            elif self.annotations is not None and len(self.annotations) != len(x_data):
                for ann in self.annotations:
                    ann.remove()
                self.annotations = []


    def markPeaks(self, peaksCoordinates,ax_index = 0):
        x_data, y_data = zip(*peaksCoordinates) # turns [(x0,y0),(x1,y1)] into [(x0,x1),(y0,y1)]
        # if scatter don't exist - scatter for the first time
        if not self.markedPeaks:
            # draw scatter + define style
            self.markedPeaks = self.axes[ax_index].scatter(x_data, y_data, marker="o", color="r")
        else:  # merely update location
            self.markedPeaks.set_offsets(np.c_[x_data, y_data])  # this seems to work.

    def annotateWithArrow(self, x,y, ax_index = 0):
        return(self.axes[ax_index].annotate('', xy=(x, y),  xycoords='data',
            xytext=(0.8, 0.95), textcoords='axes fraction',
            arrowprops=dict(facecolor='black', shrink=0.05),
            horizontalalignment='right', verticalalignment='top'))

    def addTextBox(self, textstr):
        props = dict(boxstyle='round', facecolor='grey', alpha=0.1)
        self.textBox = self.axes[0].text(0.05, 0.95, textstr, transform=self.axes[0].transAxes, fontsize=32,
        verticalalignment='top', bbox=props)

    def plotVerticalLines(self, **kwargs):
        if 'redraw' in kwargs and kwargs['redraw'] and 'verticalXs' in kwargs and type(kwargs['verticalXs']) is list:
            style = kwargs['vLineStyle'] if 'vLineStyle' in kwargs else '-'
            for x in kwargs['verticalXs']:
                self.axes[0].axvline(x,linestyle = style)

    # TODO: this here is old Jeremy code. clean it up! does this belong here? this should be scope!
    def plotDataPGC(self, im, axSigma=None, aoe=None):

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
        ax1.imshow(m, interpolation='none', cmap='rainbow')
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

    def plotImages(self, im, axSigma=None, aoe=None):
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


