
from PyQt5 import uic
from scipy import optimize,spatial
from scipy.signal import find_peaks
from scipy.constants import h
import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import matplotlib
from PyQt5.QtCore import QThreadPool

_CONNECTION_ATTMPTS = 2

try:
    from functions.cavity_lock.cavity_lock import CavityLock
except:
    print("Run without calculate OD")
if matplotlib.get_backend() != 'Qt5Agg':
    matplotlib.use('Qt5Agg')

from widgets.scopeWidget.scope import Scope_GUI


class OD_GUI(Scope_GUI):
    def __init__(self, Parent=None, ui=None, simulation=True, RedPitayaHost = None, debugging = False, sensitivity = (2.41e5,2.41e5)):
       # 2.24541949e+04 From second msrmnt
       # 2.8e4 From first msrmnt
       # I settle for 2.5
        if Parent is not None:
            self.Parent = Parent

        self.nRangesToSelect = 3 # We select three ranges: msrmnt, reference, dark count
        self.rangeSelectionLineStyle = '--'
        self.listenForMouseClickCID = None
        self.listenForMouseMoveCID = None
        self.selectedXRanges = None # containing pairs of (x_start, x_end) (in data units) defining ranges on scope
        self.vLineMarker = None

        if __name__ == "__main__":
            self.threadpool = QThreadPool()
            print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        super().__init__(Parent=Parent, ui=ui, simulation=simulation, RedPitayaHost = RedPitayaHost, debugging=debugging)

        # Add outputs control UI
        self.ODControl=self.frame_4
        ui_outputs = os.path.join(os.path.dirname(__file__), "ODControls.ui")
        uic.loadUi(ui_outputs, self.ODControl) # place outputs in frame 4
        self.connectOtherButtonsAndSpinboxes()

        # Hide parameters frame
        self.frame_parameters.hide()

        # Define sensitivity of detector
        self.sensitivity = sensitivity # [Volts/Watts] An array (or tuple) containing sensitivity for each channels. This should be measured in a stand-alone experiment.


    def connectOtherButtonsAndSpinboxes(self):
        self.ODControl.pushButton_selectRanges.clicked.connect(self.scopeListenForMouseEvents)
        self.ODControl.pushButton_autoSelectRanges.clicked.connect(self.scopeListenForMouseEvents)
        self.ODControl.pushButton_updateRanges.clicked.connect(self.updateSelectedRangesFromSpinboxes)

    def updateSelectedRangesFromSpinboxes(self):
        # Update @self.selectedXRanges accoridng to spinboxes, then redraw.
        s1 = self.ODControl.doubleSpinBox_range1Start.value()
        s2 = self.ODControl.doubleSpinBox_range2Start.value()
        dCountS = self.ODControl.doubleSpinBox_rangeDarkCountStart.value()
        w = self.ODControl.doubleSpinBox_rangesWidth.value()
        self.selectedXRanges = [s1, s1 + w, s2, s2 + w, dCountS, dCountS + w]
        # self.scope_parameters['new_parameters'] = True # Force redraw and delete old vertical lines
        self.CHsUpdated = True

    def updatedSpinboxesToMatchSelectedRanges(self):
        # self explenatory
        r = self.selectedXRanges
        self.ODControl.doubleSpinBox_range1Start.setValue(r[0])
        self.ODControl.doubleSpinBox_range2Start.setValue(r[2])
        self.ODControl.doubleSpinBox_rangeDarkCountStart.setValue(r[4])
        self.ODControl.doubleSpinBox_rangesWidth.setValue(r[1] - r[0])

    def scopeListenForMouseEvents(self):
        def mouseClickOnScope(event): # what should do on mouse click, when listening
            # Find nearest peak
            if type(self.selectedXRanges) is list:
               # save x data
                self.selectedXRanges.append(event.xdata)
                # Add vertical line to graph
                ax = event.inaxes  # the axes instance
                ax.axvline(event.xdata, linestyle='-', alpha = 0.5)
                if len(self.selectedXRanges) == self.nRangesToSelect * 2:
                    # If clicked on canvas, and already has two peaks selected, stop listening for click
                    self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseClickCID)
                    self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseMoveCID)
                    self.listenForMouseClickCID, self.listenForMouseMoveCID = None, None
                    # self.selectedXRanges.append(self.selectedXRanges[4] + (self.selectedXRanges[1] - self.selectedXRanges[0])) # add the final line, same distance from the third as the second is from the first
                    # ax.axvline(self.selectedXRanges[-1], linestyle=self.rangeSelectionLineStyle) # add this final line to graph
                    self.updatedSpinboxesToMatchSelectedRanges()
                    print(self.selectedXRanges)

        def mouseMoveOnScope(event):
            # get the x and y pixel coords
            if event.inaxes:
                ax = event.inaxes  # the axes instance
                if self.vLineMarker is None:
                    self.vLineMarker = ax.axvline(event.xdata,linestyle = '--', alpha = 0.5)
                else:
                    self.vLineMarker.set_xdata(event.xdata)

        self.selectedXRanges = []
        self.vLineMarker = None
        # self.scope_parameters['new_parameters'] = True # Force redraw and delete old vertical lines
        self.CHsUpdated = True # Force redraw and delete old vertical lines
        if self.listenForMouseClickCID is None:  # start listening
            self.listenForMouseClickCID = self.widgetPlot.canvas.mpl_connect('button_press_event', mouseClickOnScope)
            self.listenForMouseMoveCID = self.widgetPlot.canvas.mpl_connect('motion_notify_event', mouseMoveOnScope)
            self.print_to_dialogue('Select second peak on scope...', color='green')
        else: # stop listen
            self.vLineMarker = None
            self.widgetPlot.canvas.mpl_disconnect(self.listenForMouseClickCID)
            self.listenForMouseClickCID = None


    # Never call this method. this is called by RedPitaya
    def update_scope(self, data, parameters):
        if self.rp.firstRun:
            # Set default from display...
            self.comboBox_triggerSource.setCurrentIndex(2) # Select EXT trigger...
            self.updatePlotDisplay()
            self.setInverseChns()
            self.showHideParametersWindow()
            self.chns_update()
            self.rp.firstRun = False

        # ---------------- Handle duplicate data ----------------
        # It seems RedPitaya tends to send the same data more than once. That is, although it has not been triggered,
        # scope will send current data as fast as it can.
        # Following lines aim to prevent unnecessary work
        previousDataIndex = (self.avg_indx - 1) % self.Avg_num
        # print(data[0])
        # print(self.Rb_lines_Data[previousDataIndex])
        if not self.rp.firstRun and np.array_equal(self.Rb_lines_Data[previousDataIndex], data[0]) and np.array_equal(self.Cavity_Transmission_Data[previousDataIndex], data[1]):
            return
        # ---------------- Handle Redraws and data reading ----------------
        # This is true only when some parameters were changed on RP, prompting a total redraw of the plot (in other cases, updating the data suffices)
        redraw = (parameters['new_parameters'] or self.CHsUpdated)
        if redraw:
            self.scope_parameters.update(parameters)  # keep all the parameters. we need them.
            self.CHsUpdated = False
        self.Rb_lines_Data[self.avg_indx] = data[0]  # Insert new data
        self.Cavity_Transmission_Data[self.avg_indx] = data[1]  # Insert new data
        self.avg_indx = (self.avg_indx + 1) % self.Avg_num

        # ---------------- Average data  ----------------
        # Calculate avarage data and find peaks position (indx) and properties:
        Avg_data = []
        if self.checkBox_Rb_lines.isChecked():
            self.Rb_lines_Avg_Data = np.average(self.Rb_lines_Data, axis=0)
            Avg_data = Avg_data + [self.Rb_lines_Avg_Data]
        if self.checkBox_Cavity_transm.isChecked():
            self.Cavity_Transmission_Avg_Data = np.average(self.Cavity_Transmission_Data, axis=0)
            Avg_data = Avg_data + [self.Cavity_Transmission_Avg_Data]
        # ------- Scales -------
        # At this point we assume we have a corrcet calibration polynomial in @self.index_to_freq
        # Set Values for x-axis frequency:

        time_scale = float(self.scope_parameters['OSC_TIME_SCALE']['value'])
        indx_to_time = float(10 * time_scale / self.scope_parameters['OSC_DATA_SIZE']['value'])
        # time-scale
        x_axis = np.linspace(0, time_scale * 10, num=int(self.scope_parameters['OSC_DATA_SIZE']['value']))
        x_ticks = np.arange(x_axis[0], x_axis[-1], time_scale)
        y_scale = float(self.doubleSpinBox_VtoDiv.text())
        y_offset = float(self.doubleSpinBox_VOffset.text())
        y_ticks = np.arange(y_offset - y_scale * 5, y_offset + y_scale * 5, y_scale)

        # ----------- Calculate OD -----------
        text = None
        if self.selectedXRanges and len(self.selectedXRanges) == 6: # that is, if there are two ranges selected
            if self.ODControl.radioButton_OD.isChecked():
                OD = self.calculateOD(data=Avg_data, x_axis=x_axis, channel=2)
                text = 'OD = %.2f' % OD
            elif self.ODControl.radioButton_Depump.isChecked():
                depump = self.calculateDepump(data=Avg_data, x_axis=x_axis, channel=1)
                text = 'Depump = %.2f' % (depump / 1e6)

        # ----------- text box -----------
        # to be printed in lower right corner
        text_box_string = text

        # --------- plot ---------
        # Prepare data for display:
        labels = ["CH1 - Depump", "CH2 - OD"]
        self.widgetPlot.plot_Scope(x_axis, Avg_data, autoscale=self.checkBox_plotAutoscale.isChecked(), redraw=redraw, labels = labels, x_ticks = x_ticks, y_ticks= y_ticks,
                                   text_box = text_box_string, aux_plotting_func=self.widgetPlot.plotVerticalLines, verticalXs = self.selectedXRanges, vLineStyle = self.rangeSelectionLineStyle)

        # -------- Save Data  --------
        #TODO fix this. Seperate common scope actions and speciality features... this should not be copied from the scope.py method
        if self.checkBox_saveData.isChecked() or self.isSavingNDataFiles:
            self.saveCurrentData(text_box_string)

    def calculateDepump(self, data, x_axis, channel = 1):
        i = channel - 1
        if i not in (0,1): self.print_to_dialogue('Error in calculateOD, check channel.', color='red')
        d = np.array(data[i])
        s = self.sensitivity[i]
        # h is planck's constant; see import at the top; in [J] * [sec]
        f = 384.230e12 - 2.563e9 + 266.650e6 # frequency of depump transition
        #dT = (self.selectedXRanges[1] - self.selectedXRanges[0]) / len(d[np.where(np.logical_and(x_axis > self.selectedXRanges[0], x_axis < self.selectedXRanges[1]))])
        dT = x_axis[1] - x_axis[0]
        d = d * dT * 1e-3 # Time is in ms
        integral1 = np.sum(d[np.where(np.logical_and(x_axis > self.selectedXRanges[0], x_axis < self.selectedXRanges[1]))])
        integral2 = np.sum(d[np.where(np.logical_and(x_axis > self.selectedXRanges[2], x_axis < self.selectedXRanges[3]))])
        N = (integral2 - integral1) / (2 * s * h * f)
        return N

    def calculateOD(self, data, x_axis, channel = 1):
        i = channel - 1
        if i not in (0,1): self.print_to_dialogue('Error in calculateOD, check channel.', color='red')
        d = np.array(data[i])
        # h is planck's constant; see import at the top
        f = 384.230e12 - 2.563e9  # frequency of OD transition
        # darkCount = np.mean(d[np.where(np.logical_and(x_axis > (self.selectedXRanges[3] + self.selectedXRanges[2] - self.selectedXRanges[1]), x_axis < (self.selectedXRanges[3] + self.selectedXRanges[2] - self.selectedXRanges[0])))])
        ODMsmnt = np.mean(d[np.where(np.logical_and(x_axis > self.selectedXRanges[0], x_axis < self.selectedXRanges[1]))])
        refMsmnt = np.mean(d[np.where(np.logical_and(x_axis > self.selectedXRanges[2], x_axis < self.selectedXRanges[3]))])
        # darkCount = np.mean(d[np.where(np.logical_and(x_axis > self.selectedXRanges[4], x_axis < self.selectedXRanges[5]))])
        darkCount = np.mean(d[np.where(np.logical_or(x_axis < self.selectedXRanges[0], x_axis > self.selectedXRanges[3]))])
        N = np.log(np.abs(refMsmnt - darkCount) / np.abs(ODMsmnt - darkCount))
        return N

if __name__ == "__main__":
    app = QApplication([])
    simulation = False if os.getlogin() == 'orelb' else True
    window = OD_GUI(simulation=simulation, RedPitayaHost = 'rp-f08c22', debugging= True)
    # Typical OD values: V = 20mV, time-div = 0.2ms, offset = -80mV
    window.show()
    app.exec_()
    sys.exit(app.exec_())