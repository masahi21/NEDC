#!/usr/bin/python3
from __future__ import division, print_function
# from globalvalues import DEFAULT_DATALOG_D3S
import numpy as np
# from pandas import DataFrame
#import matplotlib
#matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib
matplotlib.rcParams['toolbar'] = 'None'
# import seaborn as sns
# from ggplot import *
#from mpltools import style
#from mpltools import layout
import time
import Tkinter
# from PySide.QtGui import QApplication
#from PyQt5.QtWidgets import QApplication

from auxiliaries import datetime_from_epoch
from auxiliaries import set_verbosity
from collections import deque


class Real_Time_Spectra(object):
    """
    Class to control the real time spectra plotting
    """

    def __init__(self, manager=None, verbosity=1, logfile=None,
                 resolution=256):
        """Initiate class variables."""

        self.v = verbosity
        if manager and logfile is None:
            set_verbosity(self, logfile=manager.logfile)
        else:
            set_verbosity(self, logfile=logfile)

        self.manager = manager

        self.interval = manager.interval
        self.queue = deque()

        self.maxspectra = manager.maxspectra

        self.maxspectra = manager.maxspectra

        self.data = None
        self.resolution = resolution

        self.first = True

        self.waterfall_drawn = False
        self.colorbar_drawn = True

        self.disp_count = list()
        self.time_stamp = list()

        plt.ion()

    def setup_window_geo(self, x_pos_scaling=0.0, y_pos_scaling=0.0, \
                         width_scaling=1.0, height_scaling=1.0):
        '''
        Setup the geometry (position and size) of the last initialized figure
        window.
        Default: Top-left corner position and fullscreen size
        '''

        '''
        Get the current figure manager for plotting.
        '''
        plot_manager = plt.get_current_fig_manager()

        '''
        Set the position and size of the waterfall plot based on the input
        scaling values.
        '''
        x_pos = int(x_pos_scaling * self.screen_width)
        y_pos = int(y_pos_scaling * self.screen_height)
        width = int(width_scaling * self.screen_width)
        height = int(height_scaling * self.screen_height)

        '''
        Apply the changes to the window geometry.if self.colorbar_drawn:
            self.cb = plt.colorbar()
            self.colorbar_drawn = False
        if not self.colorbar_drawn:
            self.cb.remove()
            self.cb = plt.colorbar()
        '''
        plot_manager.window.setGeometry(x_pos, y_pos, width, height)

    def start_up_plotting(self):
        '''Set up the new plotting windows using mpltools with a ggplot theme'''

        '''
        Create a QApplication so we can use PySide to find the screen size.
        '''
        app = QApplication([])

        '''
        Get the screen geometry
        '''
        scr_geo = app.desktop().screenGeometry()

        '''
        Return the screen width and height (in pixels) from the attributes of
        the screen geometry.
        '''
        self.screen_width, self.screen_height = scr_geo.width(), scr_geo.height()

        '''
        Use the ggplot style available though the mpltools layout method.
        '''
        style.use('ggplot')

        """
        Removes toolbar from figures.
        """
        plt.rcParams['toolbar'] = 'None'

        '''
        Turn on interactive mode for plotting to allow for two figure windows
        to be open at once.
        '''
        plt.ion()

        '''
        Setup the plot for the waterfall graph.
        '''
        plt.figure(1)

        '''
        Label the axes.
        '''
        plt.xlabel('Bin')
        plt.ylabel('Time (s)')

        '''
        Change the window geometry (position and size) using the proper scaling
        factors.
        '''
        self.setup_window_geo(0.08, 0.32, 0.36, 0.36)

        '''
        Draw the blank canvas figure for the spectrum plot and store it as the
        second figure window.
        '''
        plt.figure(2)

        '''
        Change the window geometry (position and size) using the proper scaling
        factors.
        '''
        self.setup_window_geo(0.56, 0.32, 0.36, 0.36)


    def add_data(self, queue, spectra, maxspectra):
        """
        Takes data from datalog and places it in a queue. Rebin data here.
        Applies to waterfall plot.
        """

        '''
        Create a new spectrum by binning the old spectrum.
        '''
        new_spectra = self.rebin(spectra)

        '''
        Add the new spectrum to queue.
        '''
        queue.append(new_spectra)
        self.time_stamp.append(datetime_from_epoch(time.time()))
        self.disp_count.append(sum(spectra))

        '''
        Save the original size of the data queue.
        '''
        data_length = len(queue)

        '''
        Pop off the first data point if the total number of counts in the
        spectrum is more than the count window defined by the sum interval
        to create a running average.
        '''
        if data_length > maxspectra:
            queue.popleft()
        if len(self.time_stamp) > maxspectra:
            self.time_stamp = self.time_stamp[1:]
            self.disp_count = self.disp_count[1:]

        self.run_avg, self.sum_data = self.run_avg_data(self.queue)

        self.make_image()


    def run_avg_data(self, data):
        """
        Calculates a running average of all the count data for each bin in the
        queue.
        """

        '''
        Calculate the running average as the mean of each element in the
        summation of the spectra in the temporary data array.
        '''
        running_avg_array = np.array(data).sum(axis = 0)/ len(data)

        '''
        Calculate the sum of the spectra.
        '''
        sum_data = sum(data)

        '''
        Return the running average and summation data.
        '''

        return running_avg_array, sum_data

    def close(self,plot_id):
        plt.close(plot_id)



    def rebin(self, data, n=4):
        """
        Rebins the array. n is the divisor. Rebin the data in the grab_data
        method.
        """
        a = len(data)/n

        new_data = np.zeros((self.resolution, 1))

        i = 0

        count = 0

        while i < a:

            temp = sum(data[i:n*(count+1)])

            new_data[count] = temp

            count += 1

            i += n

        return new_data

    def make_image(self):
        """
        Prepares an array for the waterfall plot
        """
        if self.first:

            self.first = False
            self.data = self.fix_array()

        else:

            self.data = np.concatenate((self.fix_array(), self.data), axis=0)

            '''
            Removes oldest spectra to keep size equal to maxspectra
            '''
            if len(self.data) > self.maxspectra:
                self.data = self.data[:-1]


    def fix_array(self):
        """
        Used to format arrays for the waterfall plot.
        """
        new_array = np.zeros((1, self.resolution), dtype = float)
        new_array[0, :] = np.ndarray.flatten(self.queue[-1])

        return new_array

    def sum_graph(self, data):
        """Prepares plot for sum graph."""

        '''
        Switch to working on the spectrum figure window.
        '''
        plt.figure(2)
        fig = plt.figure(2)
        fig.canvas.set_window_title('Spectrum')
        gs = GridSpec(12,1)

        ax1 = fig.add_subplot(gs[1:7,:])
        ax2 = fig.add_subplot(gs[6:10,:])
        ax3 = fig.add_subplot(gs[0,:])


        '''
        Set the labels for the spectrum plot.
        '''
        ax1.set(xlabel = 'Channel', ylabel = 'Counts')
        ax2.set(xlabel = 'Time', ylabel = 'Counts')

        '''
        Set a logarithmic y-scale.
        '''
        ax1.set_yscale('log')

        '''
        Create the x-axis data for the spectrum plot.
        '''
        x = np.linspace(0, 4096, 256)


        '''
        Plot the spectrum plot.
        '''
        ax1.plot(x, data, drawstyle='steps-mid')

        ax2.plot(self.time_stamp, self.disp_count)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        ha = 'horizontalalignment'

        display = int(self.disp_count[-1])
        dose = round(display * 0.0000427*60,4)
        dose_display = str(dose) + " $\mu$Sv/hr"

        ax3.set_axis_off()
        if display <= 150:
            ax3.text(0.1, 1.2,"Counts: "+ str(display), fontsize = 14 , ha = "center", backgroundcolor = "lightgreen")
            ax3.text(0.7, 1.2,"Dose: "+ dose_display, fontsize = 14, ha = "center", backgroundcolor = "lightgreen")

        elif display > 150 and display <= 500:
            ax3.text(0.1, 1.2,"Counts: "+str(display), fontsize = 14, ha = "center", backgroundcolor = "yellow")
            ax3.text(0.7, 1.2,"Dose: "+dose_display, fontsize = 14, ha = "center" , backgroundcolor = "yellow")


        elif display > 500 and display <= 2000:
            ax3.text(0.1, 1.2,"Counts: "+str(display), fontsize = 14, ha = "center", backgroundcolor = "orange")
            ax3.text(0.7, 1.2,"Dose: "+dose_display, fontsize = 14, ha = "center",  backgroundcolor = "orange")


        elif display > 2000:
            ax3.text(0.2, 1.2,"Counts: "+str(display), fontsize = 14, ha = "center" , backgroundcolor = "red")
            ax3.text(0.7, 1.2,"Dose: "+dose_display, fontsize = 14, ha = "center", backgroundcolor = "red")

        '''
        Resize the plot to make room for the axes labels without resizing the
        figure window.
        '''

        plt.tight_layout(h_pad = 1.5)




    def plot_waterfall(self,plot_id):
        plt.figure(plot_id)
        fig = plt.figure(plot_id)
        fig.canvas.set_window_title('Waterfall')

        """
        Plots the data for the waterfall plot.
        """
        if not self.waterfall_drawn:
            self.waterfall_plot = plt.imshow(self.data,
                                             interpolation='nearest',
                                             aspect='auto',
                                             extent=[1, 4096, 0,
                                             np.shape(self.data)[0]
                                             * self.interval])
            self.waterfall_drawn = True
            self.cb = plt.colorbar()

        else:
            self.waterfall_plot.autoscale()
            self.waterfall_plot.set_data(self.data)
            self.cb.remove()
            self.cb = plt.colorbar()


        """
        Updates the colorbar by removing old colorbar.
        """
        # if self.colorbar_drawn:

        #     self.cb = plt.colorbar()
        #     self.colorbar_drawn = False

        # else:

        #     self.cb.remove()
        #     self.cb = plt.colorbar()

        plt.tight_layout()

        plt.show()

        plt.pause(0.0005)

    def plot_sum(self,plot_id,):
        """
        Plot the sum (spectrum) figure.
        """

        '''
        Point to the figure window for the spectrum plot.
        '''
        plt.figure(plot_id)


        '''
        Clear the prior spectrum figure.
        '''
        plt.clf()
        '''
        Plot the spectrum figure
        '''
        self.sum_graph(self.run_avg)

        '''
        Show the updated spectrum figure window.
        '''
        plt.show()
        '''
        Pause before displaying the next figure window.
        '''
        plt.pause(0.0005)

        # plt.close()
