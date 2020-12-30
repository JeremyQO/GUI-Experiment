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

from PyQt5 import uic, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication

import sys
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

Form, Window = uic.loadUiType("C:\\Users\\Jeremy\\Dropbox\\python_postdoc\\temperature\\experiment.ui")


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, axis = None, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        if axis is None:
            self.axes = fig.add_subplot(111)
            self.axes.set_title("Title $\\mu$")
        super(MplCanvas, self).__init__(fig)


class experiment_gui:
    def __init__(self):
        app = QApplication([])
        window = Window()
        self.form = Form()
        self.form.setupUi(window)
        self.form.pushButton.clicked.connect(self.prin)
        
        sc = MplCanvas(parent=window, width=12.4, height=8.0, dpi=100)
        # dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\Images'
        # self.ims = images(dirname, imrange=[0,19])
        # stds_y = [el.std_y for el in self.ims.images]
        # sc.axes.plot(self.ims.times, stds_y, 'or')

        sc.axes.plot([1,4,2,3])        
        
        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(sc, window)
        
        # layout = self.form.verticalLayout_mpl
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)
        
        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        
        self.form.verticalLayout_mpl.addWidget(widget)
        
        # window.setCentralWidget(widget)
        
        window.show()
        app.exec_()

    def prin(self):
        print("sucess")

o = experiment_gui()

