import vxi11 # https://github.com/python-ivi/python-vxi11
import numpy as np
import matplotlib.pyplot as plt
from datetime import date,datetime
import time
import os
from lorentizansFit import multipleLorentziansFitter
from scipy.fft import rfft,rfftfreq, irfft # from signal cleanup


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



class DPO7254Visa():
    def __init__(self, ip = '169.254.231.198'):
        self.scope = vxi11.Instrument(ip)
        self.write('*CLS') # clear EVERYTHING!
        self.ID = self.ask("*IDN?")
        self.dataString = ''
        if 'TEKTRONIX,DPO7254' not in self.ID:
            printError('Could not identify instrument. Check connection, try again.')
            return
        printGreen(self.ID)
    # Following are two scriptting shortcuts
    def ask(self, s): return(self.scope.ask(s))
    def write(self, s): self.scope.write(s)

    # Acquire data from a specific channel
    def acquireData(self, ch=1):
        if ch not in [1,2,3,4]:
            printError('Wrong channel!')
            return
        self.write('WFMOUTPRE:ENCDG ASCii') # send back data in ascii
        self.write('DATA:SOURCE CH{}'.format(int(ch)))
        self.source = self.ask('DATA:SOURCE?')


        # First we get back a few acquistion parameters
        aParams = self.ask('WFMOutpre?').split(';')
        assert aParams[8] =='"s"' and aParams[-5] =='"V"' # make sure we are working with seconds and volts scale; if this line raises an error, scope must be returning other units
        nDataPoints, xMulti = int(aParams[6]), float(aParams[9]) # number of points in WVFM; Time scale multiplier
        yMult, yDigOff, yOffset = float(aParams[-4]),float(aParams[-3]), float(aParams[-2]) # Digital (arbitrary) scale to volts. multiplier, arbitrary offset, offset in volts
        self.write('DATA:STOP {}'.format(nDataPoints*2)) # make sure we bring back entire data
        # Acquisition
        dataString = self.ask('CURVE?') # acquire data
        self.timeData = np.linspace(start = 0, stop = nDataPoints * xMulti, num = nDataPoints) # create time scale
        self.wvfm = (np.fromstring(dataString, dtype = int,sep=',') - yDigOff) * yMult         # get data in volts
        if self.ask('*ESR?') == '0': # check for error codes etc. If all is right, answer should be 0
            printGreen('Acquisition from {} successful'.format(self.source))
        else: printError('Acquisition from {} failed'.format(self.source))

    # Plot last received data
    def plotData(self, show = True):
        now = datetime.now()
        nowformated = now.strftime("%m/%d/%Y, %H:%M:%S")
        plt.plot(scope.timeData, scope.wvfm)
        plt.xlabel('Time [sec]')
        plt.ylabel('Voltage [V]')
        plt.title(str(self.source) + '\n%s' %str(nowformated) )
        plt.grid(True)
        if show:
            plt.show()

    def saveData(self):
        now = datetime.now()
        today = date.today()
        datadir = os.path.join("C:\\", "Pycharm", "Expriements", "DATA", "DPO7254")
        todayformated = today.strftime("%B-%d-%Y")
        todaydatadir = os.path.join(datadir, todayformated)
        nowformated = now.strftime("%Hh%Mm%Ss")
        try:
            os.makedirs(todaydatadir)
            print("Created folder DATA/FPO7254/%s" % (todayformated))
            print("Data Saved")
        except FileExistsError:
            print("Data Saved")

        self.datafile = os.path.join(todaydatadir, nowformated + ".txt")
        meta = "Traces from the DPO7254 scope, obtained on %s at %s.\n" % (todayformated, nowformated)
        np.savez_compressed(os.path.join(todaydatadir, nowformated), Data=self.wvfm,time=self.timeData, meta=meta)

# scope = DPO7254Visa(ip = '169.254.231.198')
scope = DPO7254Visa(ip = '132.77.55.137')
accDelay = 3 * 60 # 3 minutes

def savePlotsAndData():
    plt.clf() # clear all existing figures.
    # ------ Data acquire ------
    scope.acquireData(ch = 2)
    scope.saveData()
    time.sleep(1)
    scope.plotData(show = False)
    scope.acquireData(ch = 1)
    scope.saveData()
    scope.plotData(show = False)
    #plt.scatter(x = scope.timeData[lf.peaks_indices], y = scope.wvfm[lf.peaks_indices],color='black')

    # ----- Date-Time & Path ------
    # TODO: Remove code duplicacy with save above...
    datadir = os.path.join("U:\\", "Lab_2021-2022","DATA", "DPO7254")
    now = datetime.now()
    today = date.today()
    todayformated = today.strftime("%B-%d-%Y")
    todaydatadir = os.path.join(datadir, todayformated)
    try:
        os.makedirs(todaydatadir)
        print("Created folder DATA/FPO7254/%s" % (todayformated))
        print("Figure Saved")
    except FileExistsError:
        print("Figure Saved")

    nowformated = now.strftime("%H-%M-%S")
    figPath = os.path.join(todaydatadir, nowformated + ".png")
    plt.savefig(figPath, dpi=300, format='png', pad_inches=0.1)
    time.sleep(accDelay) # wait for @accDelay before next reading

defDirectory = 'C:\\Pycharm\\Expriements\\DATA\\DPO7254\\'
def loadData(file):
    npData = np.load(file)
    data = npData['Data']
    time = npData['time']
    return(time, data)
# ch1File =  defDirectory + 'February-20-2022\\' + '09h31m41s' + '.npz'
# ch2File =  defDirectory + 'February-20-2022\\' + '09h31m42s' + '.npz'

# time, ch1 = loadData(ch1File)

while(True):
    savePlotsAndData()
#plt.show()