#import pyautogui
import pyvisa as visa
from simple_pid import PID
import numpy as np
from matplotlib import pyplot as plt
import instruments # Note: install GitHub latest version using the command (in Windows console, must have Git installed): pip install git+https://www.github.com/instrumentkit/InstrumentKit.git#egg=instrumentkit
import cv2
import time

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QShortcut, QListWidgetItem
import matplotlib

if matplotlib.get_backend()!='Qt5Agg':
    matplotlib.use('Qt5Agg')

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

class Keithley3390Controller():
    __instID = 'Keithley Instruments Inc.,3390,1194979,1.02-0B1-03-02-02'
    def __init__(self, host = 'USB0::0x05E6::0x3390::1194979::INSTR'):
        self.rm = visa.ResourceManager()
        self.AWG = self.rm.open_resource(host)
        ID = self.AWG.query("*IDN?").strip()
        if ID != self.__instID: printError('Could not connect to AWG! ID: %s' % ID)
        else: printGreen('Connected to AWG successfully!')
        self.recallStateFromMemory() # recall saved settings
        
    def trigger(self): self.AWG.write('*TRG')
    def recallStateFromMemory(self, state = 3): self.AWG.write('*RCL %d' %int(state))
        
class Picomotor8742Controller():
    def __init__(self, ip = '169.254.13.33', port = 23):
        self.controller = instruments.newport.PicoMotorController8742.open_tcpip(ip, port)
        self.axes = self.controller.axis
        self.step_to_um = 0.03 # conversion of one step to micro-meter (10e6), measured by Natan at 13/4/2022; further calibration may be n order
    # -- Relative movement ---
    def xMoveStep(self, step): self.axes[0].move_relative = step
    def yMoveStep(self, step): self.axes[1].move_relative = step
    def xMoveDistance(self, d): self.axes[0].move_relative = d / self.step_to_um
    def yMoveDistance(self, d): self.axes[1].move_relative = d / self.step_to_um
    # -- Absolute Movement --- 
    def xMoveTo(self, x): self.axes[0].move_absolute  = x
    def yMoveTo(self, y): self.axes[1].move_absolute  = y
    # --- Absolute position --- 
    def getXPosition(self): return(self.axes[0].position)
    def getYPosition(self): return(self.axes[1].position)

    
#picoC = Picomotor8742(ip = '169.254.13.33')


class ReflowController(QWidget):
    __thresholdInPixels = 1 # distance between center of current toroid and target
    __distanceToroidsInRow = 500   # um
    __distanceRowsOfToroids = 2000 # um
    __toroidsInRow = 18
    __rowsOfToroids = 2
    def __init__(self):
        super(ReflowController, self).__init__()
        ui = os.path.join(os.path.dirname(__file__), "reflowWidget.ui") if ui is None else ui
        uic.loadUi(ui, self)

        self.widgetPlot = dataplot.PlotWindow()
        self.__imagesPath = r'C:\\Users\\gabrielg.WISMAIN\\Desktop\\CO2 alignment - Python\\photos\\04142022\\N7 - chip'
        self.AWG = Keithley3390Controller()
        self.motors = Picomotor8742Controller()
        self.screenShotRegion=(385,75,1130,845) # This could be selected and changed - the frame of the screen from which image is take
        
    def grabImage(self):return(pyautogui.screenshot(region = self.screenShotRegion))
    def saveImage(self, image, fileName):
        cv2.imwrite(self.__imagesPath + '\\' + fileName + '.png', image)
    
    # Returns an array of circles detected in @img. Note: parameters are very important for the success of algo.
    # @brightness_threshold - the threshold for white vs black (above -> white; below -> black)
    # @param1, @param2 (smaller value-> more false circles), @minRadius, @maxRaius, @minDist - These are all important parameters for circle detection
    # Note: the beaviour is not clear. e.g., changing maxRadius (say, from 500 to 100) could also affect detection of smaller circles (say, of rasdius 30)
    # Play with parameters until you find exactly one circle, if possible
    def detectCircles(self, img =None, brightness_threshold = 130, minDist = 100, param1 = 50, param2 = 10, minRadius = 20, maxRadius = 100):
        if img is None: img = self.grabImage()
        
        # im1 = cv2.imread('captureToroid.PNG')
        # ------- Convert and filter image ------
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY) # convert for cv2 (to grayscale)
        blackAndWhite = cv2.inRange(img, brightness_threshold, 255) # Create a mask - this turns the photo to B&W (no grays!)
        blurred = cv2.medianBlur(blackAndWhite, 25)  # Blur everything. This is important for circle detection and noise filtering
        #cv2.bilateralFilter(gray,10,50,50)
##        plt.imshow(blurred)
##        plt.show()
        # ------- Detect circles! -------
        # docstring of HoughCircles: HoughCircles(image, method, dp, minDist[, circles[, param1[, param2[, minRadius[, maxRadius]]]]]) -> circles
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, minDist, param1=param1, param2=param2, minRadius=minRadius, maxRadius=maxRadius)

        # ------- Draw circles on image ---- 
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0,:]:
                cv2.circle(img, (i[0], i[1]), i[2], (255, 0, 0), 2)
        if circles is None: return (None,img)
        return(circles[0], img) # Note - detected circles are already added to img

    def triggerLaser(self):
        self.AWG.trigger()
        #playsound('laserSound.wav')
        printGreen('LASER!')

    def detectAndMoveCircleToTarget(self, target, showDetectedCircles = False):
        # ----- setup PID -----
        p, i, d = 5, 1, 0 # Kp, Ki, Kd
        output_limits = (self.__distanceToroidsInRow * (-0.4),self.__distanceToroidsInRow * 0.4) # don't move more than limit, in um
        xPid = PID(p, i, d, setpoint=target[0], output_limits= output_limits)
        yPid = PID(p, i, d, setpoint=target[1], output_limits= output_limits)

        iterations = 0
        while(iterations < 100):
            circles, img = self.detectCircles()
            if showDetectedCircles:
                print(circles)
                plt.imshow(img)
                plt.show()
                time.sleep(2)
            closestCircle = None            
            if circles is None or len(circles) == 0:
                printError('Could not detect circle! Try moving toroid to center manually, then hit ENTER.')
                input()
                self.detectAndMoveCircleToTarget(target) # try again
                return()
            elif len(circles) > 1: # if more than 1, find nearest to target.
                distanceToClosestCircle = 200000 # very large number
                for c in circles:
                    d = np.sqrt((target[0] - c[0])**2 + (target[1] - c[1])**2)
                    if d < distanceToClosestCircle:
                        closestCircle = c
                        distanceToClosestCircle = d
            else:
                closestCircle = circles[0]

            print(closestCircle)
            d = np.sqrt((target[0] - closestCircle[0])**2 + (target[1] - closestCircle[1])**2)
            if d < self.__thresholdInPixels: break
            
            # Note: setpoints are defined above. We input circle-center location, and the PID does the work
            self.motors.xMoveStep((-1) * xPid(closestCircle[0]))
            self.motors.yMoveStep((-1) * yPid(closestCircle[1]))      
            iterations += 1
            time.sleep(0.2) # This is necessary. There's a delay between movement and image-grabbing
            
    def moveToNextToroid(self, moveDown = False):
        __stepsToNextTorois = 4000 # move this number of steps. found toroid? good. otherwise - move on
        yDirection = (-1) if moveDown else 1
        previousToroidStillInFrame = True
        newToroidInFrame = False
        while(previousToroidStillInFrame or not newToroidInFrame):
            self.motors.yMoveStep(__stepsToNextTorois * yDirection)
            time.sleep(0.2) # This is necessary. There's a delay between movement and image-grabbing
            circles, img = self.detectCircles()
            if circles is None or len(circles) == 0:
                if previousToroidStillInFrame: previousToroidStillInFrame = False
            elif len(circles) and not previousToroidStillInFrame == 1:
                newToroidInFrame = True
                
    def reflowEntireRow(self, target = (640, 320), discsLeftInRow = 18, firstToroidNumber = 1,rowNumber = 1, moveDown = False):
        for j in range(discsLeftInRow):
            self.detectAndMoveCircleToTarget(target)
            # --------   Preform reflow ----------
            _, img = self.detectCircles()
            self.saveImage(img, 'R%d%02d before reflow' % (rowNumber,j + firstToroidNumber))
            self.triggerLaser()
            _, img = self.detectCircles()
            self.saveImage(img, 'R%d%02d after reflow' % (rowNumber, j + firstToroidNumber))
            # ------- Move to next Toroid in row (roughly, before re-adjustment) -----
            self.moveToNextToroid(moveDown)

        printGreen('Finished reflow!')


#reflowController = ReflowController()


if __name__=="__main__":
    app = QApplication([])
    window = ReflowController(ui="GUI-experiment\\widgets\\CO2Reflow")
    window.show()

#reflowController.detectAndMoveCircleToTarget(target = (646, 308), showDetectedCircles = False)
##circles, img = reflowController.detectCircles(img = cv2.imread('laserCenteredOnToroidReference.PNG'))
##print(circles)
### Show result for testing:
##cv2.imshow('img', img)
##cv2.waitKey(0)
##cv2.destroyAllWindows()
##
# Toroid 1, absolute position: (19507,-97523)
# Toroid 2, absolute position: (19541,-108421)
# Toroid 3, absolute position: (19593,-125284)
# Toroid 4, absolute position: (19624,-141928)
# Toroid 5, absolute position: (19624,-158688)


# Distance between Toroids 1 and 2, in steps: -10898 (y axis only)
# Distance between Toroids 2 and 3, in steps: -16863 (y axis only)
# Distance between Toroids 3 and 4, in steps: -16644 (y axis only)
# Distance between Toroids 4 and 5, in steps: -16760 (y axis only)

