# -*- coding: utf-8 -*-
"""
Created on Mon Jan  4 18:36:39 2021

@author: Jeremy
"""


from PIL import Image
import os 
import numpy as np
import matplotlib.pyplot as plt

from scipy import optimize
import time

def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-((x - mean)**2 / 2 / stddev**2))

class image:
    def __init__(self, npimage):
        self.npimage = npimage
        self.c_x, self.c_y = self.get_center(self.npimage)
        self.line_x, self.line_y = self.get_lines()
        self.xaxis = range(len(self.line_x))
        self.yaxis = range(len(self.line_y))
        self.popt_x, self.popt_y = self.get_popt()
        self.std_x = self.popt_x[2] 
        self.mean_x = self.popt_x[1] 
        self.std_y = self.popt_y[2] 
        self.mean_y = self.popt_y[1] 

    def get_center(self, im):
        x = np.argmax(im.sum(axis=0))
        y = np.argmax(im.sum(axis=1))
        return x, y 
    
    def get_lines(self):
        return self.npimage[self.c_y], self.npimage[:,self.c_x]
    
    def get_popt(self):
        try:
            popt_x, _ = optimize.curve_fit(gaussian, self.xaxis, self.line_x, p0=[100,self.c_x,100])
            popt_y, _ = optimize.curve_fit(gaussian, self.yaxis, self.line_y, p0=[100,self.c_y,100])
        except RuntimeError:
            popt_x = [100,self.c_x,100]
            popt_y = [100,self.c_y,100]
        return popt_x, popt_y
    
    def show(self, aoe=None):
        if aoe is not None:
            xa, xb, ya, yb = aoe
            m = self.npimage[ya:yb, xa:xb]
            plt.axvline(x=self.c_x-xa, color='red')
            plt.axhline(y=self.c_y-ya, color='red')
        else:
            m, xaxis, yaxis = self.npimage
            plt.axvline(x=self.c_x, color='red')
            plt.axhline(y=self.c_y, color='red')
        plt.imshow(m, interpolation='none')

    def plot(self):
        plt.subplot(211)
        plt.plot(self.xaxis, self.line_x, label='x axis')
        plt.plot(self.xaxis, gaussian(self.xaxis, *self.popt_x),label='STD=%.0f'%(self.std_x))
        plt.legend()
        plt.subplot(212)
        plt.plot(self.yaxis, self.line_y,label='y axis' )
        plt.plot(self.yaxis, gaussian(self.yaxis, *self.popt_y),label='STD=%.0f'%(self.std_y))
        plt.legend()
        
    def optimizing(self, aoe=None):
        ax1 = plt.subplot2grid((2, 2), (1, 1),  colspan=2, rowspan=2)
        if aoe is not None:
            xa, xb, ya, yb = aoe
            m = self.npimage[ya:yb, xa:xb]
            ax1.axvline(x=self.c_x-xa, color='red')
            ax1.axhline(y=self.c_y-ya, color='red')
        else:
            m = self.npimage
            ax1.axvline(x=self.c_x, color='red')
            ax1.axhline(y=self.c_y, color='red')
        ax1.imshow(m, interpolation='none')   
        ax2 = plt.subplot2grid((2,2),(0,1), colspan=2, rowspan=1)
        ax2.plot(self.xaxis, self.line_x, label='x axis')
        ax2.plot(self.xaxis, gaussian(self.xaxis, *self.popt_x),label='STD=%.0f'%(self.std_x))
        ax2.legend()
        ax3 = plt.subplot2grid((2,2),(1,0), colspan=1, rowspan=2)
        ax3.plot(self.yaxis, self.line_y,label='y axis')
        ax3.plot(self.yaxis, gaussian(self.yaxis, *self.popt_y),label='STD=%.0f'%(self.std_y))
        ax3.legend()
        
        ax4 = plt.subplot2grid((2, 2), (0,0),  colspan=1, rowspan=1)
        ax4.text(0.2,0.6, '$\sigma_x=%.0f$'%(self.std_x), fontsize=55,  color='black')
        ax4.text(0.2,0.2, '$\sigma_y=%.0f$'%(self.std_y), fontsize=55,  color='black')
        # plt.tight_layout()
        ax = [ax1, ax2, ax3, ax4]
        sx = self.std_x
        sy = self.std_y
        return ax, sx, sy

class images:
    def __init__(self, dirname, imrange=None, aoe=None):
        self.dirname = dirname
        self.npimages, self.background, self.times = self.get_images(imrange)
        self.images = [image(im) for im in self.npimages]
        
    def get_images(self, imrange):
        '''
        Returns numpy arrays of images with background substracted
        '''
        filenames = os.listdir(self.dirname)
        dirfilenames = [self.dirname+'\\'+ na for na in filenames] 
        images = [Image.open(name) for name in dirfilenames if "t=" in name ]
        background = np.asarray([Image.open(name) for name in dirfilenames if "background" in name ][0].convert(mode='L'),dtype=float)
        npimages = [np.asarray(im.convert(mode='L'))-background for im in images]
        times=[float(el.split('=')[-1].split('.png')[0]) for el in filenames if 't=' in el]
        if imrange is not None:
            a = imrange[0]
            b = imrange[1]
            return npimages[a:b], background, times[a:b]
        return npimages, background, times

    def plot(self):
        times = self.times
        stds_x = [el.std_x for el in self.images]
        means_x = [el.mean_x for el in self.images]
        stds_y = [el.std_y for el in self.images]
        means_y = [el.mean_y for el in self.images]
        fig, axs = plt.subplots(2, 2, figsize=[10, 6.0])
        axs[0,0].plot(times,stds_x, 'or')
        axs[0,0].set(ylabel='Standard deviation (pixels)')
        axs[0,0].set_title("Along X")
        axs[1,0].plot(times, means_x, 'og')
        axs[1,0].set(ylabel='Average (pixels)', xlabel='Time (ms)')
        axs[0,1].plot(times,stds_y, 'or')
        axs[0,1].set_title("Along Y")
        axs[1,1].plot(times, means_y, 'og')
        axs[1,1].set(xlabel='Time (ms)')
        # plt.tight_layout()
        return fig, axs 

        
        
def run_exp():
    dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\Images'
    plt.figure(figsize=[12.4, 8.0])
    while True:
        plt.clf()
        ims = images(dirname)#, imrange=[4,-4])
        _,_,_,ax = ims.images[0].optimizing()#[500,1300,500,1100])
        # plt.show()
        plt.pause(0.02)
        time.sleep(1)
        print('t')

if __name__=="__main__":
    dirname = 'C:\\Users\\Jeremy\\Desktop\\MOT_PGC_FALL\\23-12-2020'
    ims = images(dirname, imrange=[0,19])
    # ims.images[0].optimizing()
    ims.plot()
    # plt.figure(figsize=[12.4, 8.0])
    # plt.clf()
    # ax = ims.images[0].optimizing()#[500,1300,500,1100])
    # run_exp()