
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from datetime import timedelta
import sys
from time import sleep
from time import time

from androlyze import Constants
from androlyze.util import Util
from androlyze.util.StopThread import StopThread
from Queue import Empty


class AnalysisStatsView(StopThread):
    ''' Updates the progress on the command line '''
    
    def __init__(self, cnt_done, cnt_complete, analyzed_apks):
        ''' 
        Parameters
        ----------
        cnt_done : Value<int>
            Number of yet finished jobs. 
        cnt_complete : int 
            Complete count of jobs.
        analyzed_apks : Queue<FastAPK>
            Yet analyzed apks.
        '''
        
        super(AnalysisStatsView, self).__init__()
        self.start_time = time()
        
        self.cnt_done = cnt_done
        self.cnt_complete = cnt_complete
        self.cnt_analyzed_apks = analyzed_apks 
        
        self.last_analyzed_apk = "N/A"
        self.last_printed_str = ""
    
    def get_latest_analyzed_apk_name(self):
        ''' Get the latest analyze apk name '''
        try:
            fastapk = self.cnt_analyzed_apks.get_nowait() 
            if fastapk:
                self.last_analyzed_apk = fastapk.short_description()
            else:
                self.last_analyzed_apk = "N/A"
            
        except Empty:
            pass
        finally:
            return self.last_analyzed_apk
        
    def run(self):
        ''' Print progress until terminate `event` set '''

        refresh_rate = Constants.PROGRESS_REFRESH_RATE / 1000.0
        while not self.shall_terminate():
            sleep(refresh_rate)
            self.print_progess()

        # print final progress before exiting
        self.print_progess()
        sys.stderr.write("\n")

    def print_progess(self):
        ''' Show the progress on run '''
        progress_str = Util.format_progress(self.cnt_done.value , self.cnt_complete)
        time_elapsed = timedelta(seconds=round(time() - self.start_time))
        progress_str = '=> [%s | %s | %s]' % (progress_str, time_elapsed, self.get_latest_analyzed_apk_name())
        sys.stdout.write("\r" + " " * len(self.last_printed_str))
        Util.print_dyn_progress(progress_str)
        self.last_printed_str = progress_str
