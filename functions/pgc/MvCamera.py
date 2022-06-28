# This module controls the matrix vision camera. It handles taking pictures, subtracting background, create a movie, fit to gaussian and measure temprature.
# Current bugs:
# 1. when trigger is not sent the software can't communicate with the camera anymore and the driver must be re-installed.

from __future__ import print_function
import os
import platform
import string
import sys
# import all the stuff from mvIMPACT Acquire into the current scope
from mvIMPACT import acquire
# import all the mvIMPACT Acquire related helper function such as 'conditionalSetProperty' into the current scope
# If you want to use this module in your code feel free to do so but make sure the 'Common' folder resides in a sub-folder of your project then
from mvIMPACT.Common import exampleHelper
# from PyQt5.QtGui import QPixmap, QImage

# For systems with NO mvDisplay library support
import ctypes
from PIL import Image
import numpy
import os
import glob
from datetime import date, datetime
# import cv2
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as mtl
import pylab as plt
import scipy.optimize as opt
import time


class MvCamera:
    # Input:
    #   DisplayImages   - a boolean parameter that defines if the image should be displayed (might be problematic on pycharm, try on powershell/other platform)
    #   SaveImages      - a boolean parameter that defines if the image should be saved
    # def __init__(self, DisplayImages = True, SaveImages = True):
    #     # aquire control on the device from the device manager with the "aquire" function
    #     # Display&save setting
    #     self.DisplaySetting()
    #     self.DisplayImages = DisplayImages
    #     self.SaveImages = SaveImages

    # =======================================================================
    # Capture Image - this function grabs an image from the mv camera, with options to display it and save it into a png in .//Images directory
    # Input:
    #   TimeOut_ms      - time in ms for which the function waits for image on the camera.  If timeout_ms is '-1', the function's timeout interval never elapses.
    #   NumberOfFrames  - defines the number of frames the capture image function grabs.
    #   DeviceNr - device number in the MvDeviceConfigure (for managing multipule devices)
    def __init__(self, deviceNr = 0, deviceSerial = None):
        #acquire connection to the camera - must be deleted at the end of use , if not the access to the camera is denied
        self.devMgr = acquire.DeviceManager() #
        #print(self.devMgr.getDeviceByFamily("mvBlue*",0).serial.read()) # This is how one reads the serial of the first device in the device manager
        # Note: https://www.matrix-vision.com/manuals/SDK_PYTHON/classmvIMPACT_1_1acquire_1_1DeviceManager.html

        if deviceSerial:
            try:
                self.pDev = self.devMgr.getDeviceBySerial(deviceSerial)
            except:
                raise ValueError('Could not find camera. Serial seems wrong. Should look like: FF006583')
        else:
            self.pDev = self.devMgr.getDevice(deviceNr)
        if self.pDev == None:
            exampleHelper.requestENTERFromUser()
            sys.exit(-1)
            raise ValueError('Could not find camera. Serial or ID are probably wrong.')
        self.pDev.open()

        #other attributes

        #pixel formatting
        id = acquire.ImageDestination(self.pDev)
        id.pixelFormat.writeS("BGR888Packed")

        print("CameraFamily:", self.pDev.family.readS())
        print("InterfaceLayout:", self.pDev.interfaceLayout.readS())

     # =======================================================================
        # Below statement is valid for All Devices (ImageProcessing)
        # =======================================================================

        # Define the AcquisitionControl Parameters
        imgProc = acquire.ImageProcessing(self.pDev)

        # Set Saturation
        # K is the saturation factor
        # K > 1 increases saturation
        # K = 1 means no change
        # 0 < K < 1 decreases saturation
        # K = 0 produces B&W
        # K < 0 inverts color
        K = 0.500
        imgProc.colorTwistEnable.write(True)
        imgProc.setSaturation(K)  # Valid Values 0.000 to 1.000

        # =======================================================================
       # =======================================================================
        # Below statement is valid only for mvBlueCOUGAR or mvBlueFOX3(GenICam) Cameras only
        # =======================================================================
        if self.pDev.family.readS() == "mvBlueFOX3" or self.pDev.family.readS() == "mvBlueCOUGAR":
            # Define the AcquisitionControl Parameters
            self.genIcamAcqCtrl = acquire.AcquisitionControl(self.pDev)

            # Write the Exposure Settings to the Camera
            self.genIcamAcqCtrl.exposureTime.write(20000)

            # Read the Exposure Settings in the Camera
            print("Exposure:", self.genIcamAcqCtrl.exposureTime.read())

            # Define the AnalogControl Parameters
            genIcamAlgCtrl = acquire.AnalogControl(self.pDev)

            # Write the Gain Settings to the Camera
            genIcamAlgCtrl.gain.write(25.000)

            # Read the Gain Settings in the Camera
            print("Gain:", genIcamAlgCtrl.gain.read())

            # Write the Black Level Settings to the Camera
            genIcamAlgCtrl.blackLevelSelector.writeS("All")
            genIcamAlgCtrl.blackLevel.write(10.00)

            # Read the Black Level Settings in the Camera
            print("BlackLevel:", genIcamAlgCtrl.blackLevel.read())

            # Set the Trigger Mode Option for Camera
            self.genIcamAcqCtrl.triggerSelector.writeS("FrameStart")
            self.genIcamAcqCtrl.triggerMode.writeS("On")  # On; Off
            self.genIcamAcqCtrl.triggerSource.writeS("Line4")  # Line4; Software
            if self.genIcamAcqCtrl.triggerSource.readS() == "Line4":
                self.genIcamAcqCtrl.triggerActivation.writeS("RisingEdge")
            self.genIcamAcqCtrl.triggerDelay.write(0.000)
        # =======================================================================

    def CaptureImage(self, fname_t = 't', TimeOut_ms=100000, NumberOfFrames=1):
        self.fi = acquire.FunctionInterface(self.pDev)
        self.statistics = acquire.Statistics(self.pDev)
        framesToCapture = NumberOfFrames
        if framesToCapture < 1:
            print("Invalid input! Please capture at least one image")
            sys.exit(-1)

        while self.fi.imageRequestSingle() == acquire.DMR_NO_ERROR:
            # print("Buffer queued")
            pass
        pPreviousRequest = None

        exampleHelper.manuallyStartAcquisitionIfNeeded(self.pDev, self.fi)
        for i in range(framesToCapture):

            requestNr = self.fi.imageRequestWaitFor(TimeOut_ms)

            if self.fi.isRequestNrValid(requestNr):
                pRequest = self.fi.getRequest(requestNr)
                if pRequest.isOK:
                    # Display Statistics
                    if i % 10 == 0:

                        print("Info from " + self.pDev.serial.read() +
                              ": " + self.statistics.framesPerSecond.name() + ": " + self.statistics.framesPerSecond.readS() +
                              ", " + self.statistics.errorCount.name() + ": " + self.statistics.errorCount.readS() +
                              ", " + "Width" + ": " + pRequest.imageWidth.readS() +
                              ", " + "Height" + ": " + pRequest.imageHeight.readS() +
                              ", " + "Channels" + ": " + pRequest.imageChannelCount.readS())

                    # Display Image
                    # if isDisplayModuleAvailable:
                    #     display.GetImageDisplay().SetImage(pRequest)
                    #     display.GetImageDisplay().Update()

                    # For systems with NO mvDisplay library support
                    cbuf = (ctypes.c_char * pRequest.imageSize.read()).from_address(int(pRequest.imageData.read()))
                    channelType = numpy.uint16 if pRequest.imageChannelBitDepth.read() > 8 else numpy.uint8
                    arr = numpy.fromstring(cbuf, dtype=channelType)

                    # # Get the PIL Image - Mono8
                    # if pRequest.imagePixelFormat.readS() == "Mono8":
                    #     arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read())
                    #     img = Image.fromarray(arr)

                    # Get the PIL Image - BGR888Packed
                    # print(pRequest.imagePixelFormat.readS())
                    if pRequest.imagePixelFormat.readS() == "BGR888Packed":
                        arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), 3)
                        img = Image.fromarray(arr, 'RGB')

                    # # Get the PIL Image - RGBx888Packed
                    # if pRequest.imagePixelFormat.readS() == "RGBx888Packed":
                    #     arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), 4)
                    #     img = Image.fromarray(arr, 'RGBX')
                #create img_name for
                now = datetime.now()
                today = date.today()
                Img_Name = '.\Images\MVcam_photo_' + today.strftime("%b_%d_%Y_") + now.strftime(
                    "%H_%M_%S") + 't=' + fname_t + str(i) + '.png'

                if pPreviousRequest != None:
                    pPreviousRequest.unlock()

                pPreviousRequest = pRequest

                self.fi.imageRequestSingle()
            else:
                # Please note that slow systems or interface technologies in combination with high resolution sensors
                # might need more time to transmit an image than the timeout value which has been passed to imageRequestWaitFor().
                # If this is the case simply wait multiple times OR increase the timeout(not recommended as usually not necessary
                # and potentially makes the capture thread less responsive) and rebuild this application.
                # Once the device is configured for triggered image acquisition and the timeout elapsed before
                # the device has been triggered this might happen as well.
                # The return code would be -2119(DEV_WAIT_FOR_REQUEST_FAILED) in that case, the documentation will provide
                # additional information under TDMR_ERROR in the interface reference.
                # If waiting with an infinite timeout(-1) it will be necessary to call 'imageRequestReset' from another thread
                # to force 'imageRequestWaitFor' to return when no data is coming from the device/can be captured.
                print("imageRequestWaitFor failed (" + str(
                    requestNr) + ", " + acquire.ImpactAcquireException.getErrorCodeAsString(requestNr) + ")")
        exampleHelper.manuallyStopAcquisitionIfNeeded(self.pDev, self.fi)
        rc = self.fi.requestCount()
        for i in range(rc):
            self.fi.imageRequestUnlock(i)
        return img, Img_Name

    #Clear the images folder
    def clear_folder(self, pathIn = 'C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images'):
        # delete all files in the images directory
        files = glob.glob(pathIn+'\*.png')
        for f in files:
           os.remove(f)

    #saves the image
    def SaveImageT(self,img,fname_t, background = False):
        # Save image to the PC - PIL
        now = datetime.now()
        today = date.today()
        Img_Name = "C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images\ " + today.strftime("%b_%d_%Y_") + now.strftime(
            "%H_%M_%S")
        if not background:
            Img_Name +=  't=' + fname_t + '.png'
        else :
            Img_Name += "background" + '.png'
        img.save(Img_Name, 'PNG')

    def SaveImage(self,img,Img_Name):
        img.save(Img_Name, 'PNG')

    # creates a movie at pathOut from the picture at PathIn in fps - frames per second
    def FramesToMovie(self,fps=1):
        pathIn = 'C:\\Pycharm\\Expriements\\Instruments\\mvIMPACT_cam\\Images'
        pathOut = 'C:\\Pycharm\\Expriements\\Instruments\\mvIMPACT_cam\\Video\\video.avi'
        FramesPerSecond = fps
        frame_array = []
        files = [f for f in os.listdir(pathIn) if isfile(join(pathIn, f))]
        # for sorting the file names properly
        files.sort(key=lambda x: x[5:-4])
        for i in range(len(files)):
            filename = pathIn + '/' + files[i]
            # reading each files
            img = cv2.imread(filename)
            height, width, layers = img.shape
            size = (width, height)

            # inserting the frames into an image array
            frame_array.append(img)
        out = cv2.VideoWriter(pathOut, cv2.VideoWriter_fourcc(*'DIVX'), FramesPerSecond, size)
        for i in range(len(frame_array)):
            # writing to a image array
            out.write(frame_array[i])
        out.release()
        os.startfile('C:\\Pycharm\\Expriements\\Instruments\mvIMPACT_cam\\Video\\video.avi')

    #subtract all the images from background and saves them to SubtractedImages folder
    def SubtractBackground(self, Background_file_name):
        OrigPath = 'C:\\Pycharm\\Expriements\\Instruments\\mvIMPACT_cam\\Images\\OriginalImages'
        Subtractpath = '.\\Images\\SubtractedImages'
        BckgrndImg = cv2.imread('.\\Images\\OriginalImages'+Background_file_name)
        files = [f for f in os.listdir(OrigPath) if isfile(join(OrigPath, f))]
        # for sorting the file names properly
        files.sort(key=lambda x: x[5:-4])
        for i in range(len(files)):
            filename = OrigPath + '/' + files[i]
            # reading each files
            orig_img = cv2.imread(filename)
            subtracted_img = cv2.absdiff(BckgrndImg, orig_img)
            Img_Name =Subtractpath+'SubtractedImage'+str(i)+'.png'
            cv2.imwrite(Img_Name, subtracted_img)

    #fit a gaussian to subtracted images
    # INPUT:
    #   Y_PIXEL_LEN - number of vertical pixels
    #   X_PIXEL_LEN - number of horizontal pixels
    #   the name of the file for fit with png termination
    #   CROP_IMG_SIZE - the size of image in each dimension after cropping is 2*CROP_IMG_SIZE
    def GaussianFit(self, file_name_for_fit, X_PIXEL_LEN=1544, Y_PIXEL_LEN=2064, CROP_IMG_SIZE =180 ,PLOT_IMG=False, PLOT_SLICE =False):
        ImgToFit = cv2.imread('./Images/SubtractedImages/' + file_name_for_fit, 0)
        img_max_index = [np.argmax(np.sum(ImgToFit, axis=1)), np.argmax(np.sum(ImgToFit, axis=0))]
        # Parameters
        X_UPPER_BOUND = int(img_max_index[0] + CROP_IMG_SIZE)
        X_LOWER_BOUND = int(img_max_index[0] - CROP_IMG_SIZE)
        EFFECTIVE_X_PIXEL_LEN = X_UPPER_BOUND - X_LOWER_BOUND

        Y_UPPER_BOUND = int(img_max_index[1] + CROP_IMG_SIZE)
        Y_LOWER_BOUND = int(img_max_index[1] - CROP_IMG_SIZE)
        EFFECTIVE_Y_PIXEL_LEN = Y_UPPER_BOUND - Y_LOWER_BOUND

        # Create x and y indices
        x = np.linspace(0, EFFECTIVE_Y_PIXEL_LEN - 1, EFFECTIVE_Y_PIXEL_LEN)
        y = np.linspace(0, EFFECTIVE_X_PIXEL_LEN - 1, EFFECTIVE_X_PIXEL_LEN)
        x, y = np.meshgrid(x, y)
        # crop an effective image
        EffectiveImg = ImgToFit[X_LOWER_BOUND:X_UPPER_BOUND, Y_LOWER_BOUND:Y_UPPER_BOUND]
        data_noisy = EffectiveImg.ravel()

        # fit the data
        img_max_index = [np.argmax(np.sum(EffectiveImg, axis=1)), np.argmax(np.sum(EffectiveImg, axis=0))]
        initial_guess = (ImgToFit[img_max_index], img_max_index[0], img_max_index[1], EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN, 0, 10)
        popt, pcov = opt.curve_fit(self.twoD_Gaussian, (x, y), data_noisy, p0=initial_guess)

        # plot the results
        data_fitted = self.twoD_Gaussian((x, y), *popt)
        sigma = [popt[3], popt[4]]
        if PLOT_IMG:
            fig, ax = plt.subplots(1, 1)

            plt.text(0.88, 0.95, '\u03C3_x =' + '%.2f' % sigma[0] + '\n' + '\u03C3_y = ' + '%.2f' % sigma[1], color='white',
                 fontsize=16, style='italic', weight='bold', horizontalalignment='center', verticalalignment='center',
                 transform=ax.transAxes, bbox=dict(facecolor='gray', alpha=0.5))
            ax.imshow(data_noisy.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN), cmap=plt.cm.jet, origin='bottom',
                  extent=(x.min(), x.max(), y.min(), y.max()))
            ax.contour(x, y, data_fitted.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN), 8, colors='w')

            plt.show()

        if PLOT_SLICE:
            # plot slice
            mtl.figure()
            data_noisy_mat = data_noisy.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN)
            Slice = data_noisy_mat[int(EFFECTIVE_X_PIXEL_LEN / 2) - 10]
            mtl.plot(Slice)
            mtl.plot(data_fitted.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN)[int(EFFECTIVE_X_PIXEL_LEN / 2) - 10])
            plt.show()
        return popt

    # define model function and pass independant variables x and y as a list
    def twoD_Gaussian(self, x_y, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        x, y = x_y
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        g = offset + amplitude * np.exp(- (a * ((x - xo) ** 2) + 2 * b * (x - xo) * (y - yo)
                                           + c * ((y - yo) ** 2)))
        return g.ravel()

    def CalculateTemprature(self):
        pass
# =======================================================================


if __name__ == '__main__':
    cam=MvCamera()
    while True:
        cam.CaptureImage()
    del cam
#     cam.FramesToMovie()



# =================================
#   other camera parameters
# =================================
# Write the Balance Ratio Settings to the Camera
# genIcamAlgCtrl.balanceRatioSelector.writeS("Red")
# genIcamAlgCtrl.balanceRatio.write(1.963)  # Valid Values - 0.063 to 16.000
# genIcamAlgCtrl.balanceRatioSelector.writeS("Blue")
# genIcamAlgCtrl.balanceRatio.write(1.723)  # Valid Values - 0.063 to 16.000

# Read the Balance Ratio Settings in the Camera
# genIcamAlgCtrl.balanceRatioSelector.writeS("Red")
# print("BalanceRatio(Red):", genIcamAlgCtrl.balanceRatio.read())
# genIcamAlgCtrl.balanceRatioSelector.writeS("Blue")
# print("BalanceRatio(Blue):", genIcamAlgCtrl.balanceRatio.read())