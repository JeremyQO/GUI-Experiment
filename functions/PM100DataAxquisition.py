##import vxi11 # https://github.com/python-ivi/python-vxi11
##import numpy as np
##import matplotlib.pyplot as plt
##from datetime import date,datetime
##import time
##import os
##from os import listdir
##from os.path import isfile, join
##from lorentizansFit import multipleLorentziansFitter
##from scipy.fft import rfft,rfftfreq, irfft # from signal cleanup

import pyvisa
#from ThorlabsPM100 import ThorlabsPM100


# DPO programming manual:
# https://download.tek.com/manual/MSO-DPO5000-DPO7000-DPO70000-DX-SX-DSA70000-and-MSO70000-DX-Programmer-077001025.pdf
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def printError(s = ''): print(f"{bcolors.WARNING}{s}{bcolors.ENDC}")
def printGreen(s = ''): print(f"{bcolors.OKGREEN}{s}{bcolors.ENDC}")



class PM100DVisa():
    def __init__(self, port = 'USB0::0x1313::0x8078::P0028892::INSTR'):
        self.rm = pyvisa.ResourceManager()
        try:
            self.inst = self.rm.open_resource(port)
            printGreen('Connected to ' + str(self.inst.query('*IDN?')))
        except:
            printError('Cold not connect to %s. Try another port.' % port)
            for s in self.rm.list_resources():
                try:
                    print('%s identifies as: ' % str(s) ,self.rm.open_resource(str(s)).query('*IDN?'))
                except:
                    printError('Could not identify %s' %str(s))

    # returns power in Watts
    def getPower(self):
        power = self.inst.query('MEAS:POW?')
        return(float(power))


#pmd100 = PM100DVisa()