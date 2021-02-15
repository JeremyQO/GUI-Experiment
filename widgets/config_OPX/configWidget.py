# -*- coding: utf-8 -*-
"""
@author: Jeremy Raskop
Created on Fri Dec 25 14:16:30 2020

* Use JSON for keeping data fed into gui
* use https://qm-docs.s3.amazonaws.com/v0.7/config/index.html#/paths/~1/get for documentation
* Doc can easily be added to GUI

Step 1: display the dictionary
Step 2: Add possibility to add elements/pulses/waveforms...

"""

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget
import os
from widgets.config_OPX.Config import config
import sys
import json
sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


class ConfigGUI (QWidget):
    def __init__(self):
        ui = os.path.join(os.path.dirname(__file__), "config.ui")
        super().__init__()
        uic.loadUi(ui, self)
        self.currentTextList1 = None
        self.currentTextList2 = None
        self.currentTextList3 = None
        self.config = config
        
        self.listWidget_1.currentTextChanged.connect(self.changed_elements_1)
        self.listWidget_2.currentTextChanged.connect(self.changed_elements_2)
        self.listWidget_3.currentTextChanged.connect(self.changed_elements_3)
        self.pushButton_save.clicked.connect(self.save_config_file)
        self.lineEdit.returnPressed.connect(self.update_config)
        self.tabname = 'elements'
        
        for el in self.config[self.tabname]:
            self.listWidget_1.addItem(el)
        
    
    def save_config_file(self):
        # np.save("config", self.config)
        json.dump(self.config, open( "config_saved.py", 'w' ), indent=4)
        print("Saved modified configuration file")
    
    def update_config(self):
        depth = (self.currentTextList1 is not None) + (self.currentTextList2 is not None) + (self.currentTextList3 is not None)
        s = self.lineEdit.text()
        print("New value: "+str(s))
        if depth==1:
            self.config[self.tabname][self.currentTextList1] = s
        elif depth==2:
            self.config[self.tabname][self.currentTextList1][self.currentTextList2] = s
        elif depth==3:
            self.config[self.tabname][self.currentTextList1][self.currentTextList2][self.currentTextList2] = s
        # print(self.listWidget_1.)
        # self.config['elements'][self.currentTextList1][self.currentTextList2][self.currentTextList3]
    
    def changed_elements_1(self, value):
        self.listWidget_2.clear()
        self.currentTextList1 = value
        self.currentTextList2 = None
        self.currentTextList3 = None
        for el in self.config[self.tabname][value]:
            self.listWidget_2.addItem(el)
            
    def changed_elements_2(self, value):
        self.listWidget_3.clear()
        self.currentTextList2 = value
        self.currentTextList3 = None
        a = self.config[self.tabname][self.currentTextList1][value]
        if type(a) is dict:
            for el in a: 
                self.listWidget_3.addItem(el)
                self.lineEdit.clear()
        else:
            self.lineEdit.setText(str(a))
            
    def changed_elements_3(self, value):
        self.currentTextList3 = value
        a = self.config[self.tabname][self.currentTextList1][self.currentTextList2][value]
        if type(a) is not dict:
            self.lineEdit.setText(str(a))


if __name__ == "__main__":
    app = QApplication([])
    window = ConfigGUI()
    window.show()
    
    # window.temperature_connect()
    # window.get_temperature(1)
    # app.exec_()
    # sys.exit(app.exec_())