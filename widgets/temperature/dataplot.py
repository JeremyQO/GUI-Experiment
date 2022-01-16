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
def lorentzian( x, x0, a, gam ):
    return a * gam**2 / ( gam**2 + ( x - x0 )**2)


class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)

        # a figure instance to plot on
        # plt.ioff()
        plt.ion()
        self.figure = plt.figure(1)
        self.ax1 = self.figure.add_subplot(111)
        self.scatter = None # Placeholder
        self.annotations = None
        self.arrow = None
        self.textBox = None
        self.lines = []
        for i in range(4): # in principle, hold 4 places for lines. With good coding, this is not neccessary
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

    def plot_Scope(self, x_data,y_data, autoscale = False, redraw = False, **kwargs):
        if not redraw:  # meanning - merely update data, without redrawing all.
            for i, line in enumerate(self.lines):
                self.lines[0].set_ydata(y_data[0])
                # self.ax1.set_ylim(min(kwargs['y_ticks']), max(kwargs['y_ticks']))
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
                if self.arrow is None: self.annotateWithArrow(kwargs['mark_peak'][0], kwargs['mark_peak'][1])
                self.arrow.xy =  (kwargs['mark_peak'][0],kwargs['mark_peak'][1])
            if 'text_box' in kwargs and kwargs['text_box'] is not None:
                if self.textBox is None: self.addTextBox(textstr=kwargs['text_box'])
                self.textBox.set_text = str(kwargs['text_box'])
            return

        self.arrow = None # reset arrow
        self.textBox = None # reset textbox
        if 'labels' not in kwargs:
            kwargs['legend'] = False
            kwargs['labels'] = [''] * 10 # to prevent glitches

        self.ax1 = None
        self.figure.clear()
        self.scatter = None
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
        if 'scatter_x_data' and 'scatter_y_data' in kwargs and 'scatter_tags' in kwargs :
            x_data, y_data = kwargs['scatter_x_data'], kwargs['scatter_y_data']
            # if not annotations exist - annotate for the first time
            if not self.scatter:
                # draw scatter + define style
                self.scatter = self.ax1.scatter(kwargs['scatter_x_data'], kwargs['scatter_y_data'], marker="x", color="b")
                self.annotations = []
                for i, x in enumerate(x_data):
                    # annotate scatter + define style
                    self.annotations.append(self.ax1.annotate(kwargs['scatter_tags'][i], xy = (x, y_data[i]), weight='bold' ))
            # If they exist - update location
            else:
                self.scatter.set_offsets(np.c_[x_data, y_data])  # this seems to work.
                if self.annotations:
                    for i, s in enumerate(self.annotations): s.set_position((x_data[i], y_data[i]))


        # for j, tag in enumerate(peak_tags):
        #     plt.annotate(tag, (Rb_peaks[j], el[Rb_peaks[j]]))
    def annotateWithArrow(self, x,y):
        self.arrow = self.ax1.annotate('', xy=(x, y),  xycoords='data',
            xytext=(0.8, 0.95), textcoords='axes fraction',
            arrowprops=dict(facecolor='black', shrink=0.05),
            horizontalalignment='right', verticalalignment='top')
    def addTextBox(self, textstr):
        props = dict(boxstyle='round', facecolor='grey', alpha=0.1)
        self.textBox = self.ax1.text(0.05, 0.95, textstr, transform=self.ax1.transAxes, fontsize=14,
        verticalalignment='top', bbox=props)
    def plot_Cavity_Spec(self, data, freq, Rb_peaks, Rb_peaks_properties, indx_to_freq, chns_to_show, labels, cursors,
                         scaletype, autoscale=True, redraw=False):
        if not redraw:  # meanning - merely update data, without redrawing all.
            self.line1.set_ydata(data[0])
            return

        # ymin, ymax = plt.ylim()
        # xmin, xmax = plt.xlim()
        colors = ['b', 'g', 'r', 'c', 'k', 'm', 'y', 'darkorange']
        peak_tags = ['1-0', '1-0/1', '1-1', '1-0/2', '1-1/2', '1-2']
        self.ax1 = None
        self.figure.clear()
        self.ax1 = self.figure.add_subplot(111)
        # self.ax1.plot(freq,data[0])
        # print(freq, data[0])
        for i, el in enumerate(np.array(data)):
            if chns_to_show[i]:
                # plt.plot(freq, el, color=colors[i], label=labels[i])
                # plt.plot(Rb_peaks, el, color=colors[i], label=labels[i])
                if scaletype:
                    line1, = self.ax1.plot(freq, el, color=colors[i], label=labels[i])  # Returns a tuple of line objects, thus the comma
                    self.ax1.set_xlim(freq[0], freq[-1])
                else:
                    line1, = self.ax1.plot(el, color=colors[i], label=labels[i])  # Returns a tuple of line objects, thus the comma
                self.line1 = line1
                self.ax1.set_ylim(0, 0.25)


                if labels[i] == "CH1 - Vortex Rb lines":
                    if scaletype:
                        plt.scatter(freq[Rb_peaks], el[Rb_peaks], marker="x", color="C1")
                        for j, tag in enumerate(peak_tags):
                            plt.annotate(tag, (freq[Rb_peaks[j]], el[Rb_peaks[j]]))
                    else:
                        plt.scatter(Rb_peaks, el[Rb_peaks], marker="x", color="C1")
                        for j, tag in enumerate(peak_tags):
                            plt.annotate(tag, (Rb_peaks[j], el[Rb_peaks[j]]))
                    # plt.vlines(x=freq[Rb_peaks], ymin=el[Rb_peaks] - Rb_peaks_properties["prominences"],
                    #            ymax=el[Rb_peaks], color="C1")
                    # plt.hlines(y=Rb_peaks_properties["width_heights"], xmin=(Rb_peaks_properties["left_ips"] * indx_to_freq),
                    #            xmax=(Rb_peaks_properties["right_ips"] * indx_to_freq), color="C1")

        # if not autoscale:
        #     plt.ylim(ymin, ymax)
        #     plt.xlim(xmin, xmax)
        if cursors:
            for curs in cursors:
                plt.axvline(curs, c='r')
        # plt.ylabel('Voltage [V]')
        # plt.xlabel('Time [ms]')
        # # plt.xlabel('Frequency [$MHz$]')
        plt.legend(loc = 'lower left')
        self.ax1.grid()
        self.ax1.grid()
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
        print(truthiness)
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
            self.ax2.set_ylim(y1min / sensitivity * 1e6, y1max / sensitivity * 1e6)

        if nathistory is not None:
            if xaxis_history == []:
                self.ax3.plot([float(el / 1e6) for el in nathistory])
                self.ax3.plot([float(el / 1e6) for el in nathistory], 'or')
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

    def plot_CavityLock_traces(self, data, time, truthiness, labels, cursors, autoscale=True, sensitivity=None,
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
        if cursors:
            for curs in cursors:
                self.ax1.axvline(curs, c='r', linestyle='--', alpha=0.4)

        if sensitivity is not None:
            self.ax2 = self.ax1.twinx()
            self.ax2.set_ylabel('Power (uW)')
            y1min, y1max = self.ax1.get_ylim()
            self.ax2.set_ylim(y1min / sensitivity * 1e6, y1max / sensitivity * 1e6)

        if nathistory is not None:
            if xaxis_history == []:
                self.ax3.plot([float(el / 1e6) for el in nathistory])
                self.ax3.plot([float(el / 1e6) for el in nathistory], 'or')
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


