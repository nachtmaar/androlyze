
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from datetime import timedelta
from multiprocessing import Value, Lock
import sys
from time import time, sleep

from androlyze import Constants
from androlyze.util import Util
from androlyze.util.StopThread import StopThread

class AnalysisStatsView(StopThread):
    ''' Thread showing current analysis progress.
    Also keeps track of succesful and failed tasks count.
    '''

    def __init__(self, cnt_total_tasks, tasks_per_chunk = 1, result = None):
        '''
        Parameters
        ----------
        cnt_total_tasks : int
            Number of total tasks.
        tasks_per_chunk : int, optional (default is 1)
            Number of subtasks a task (chunk) contains.
        results : GroupResult
            Collection of the tasks.
        '''
        super(AnalysisStatsView, self).__init__()

        self.cnt_total_task = cnt_total_tasks

        # progress stats
        self.successful_tasks = self.failed_tasks = 0

        self.tasks_per_chunk = tasks_per_chunk

        self.start_time = time()

        self.results = result

        # shared memory count of analyzed apks
        self.__analyzed_cnt_sm = Value('i', 0, lock = Lock())

    def get_cnt_total_task(self):
        return self.__cnt_total_task

    def get_successful_tasks(self):
        return self.__successful_tasks

    def get_failed_tasks(self):
        return self.__failed_tasks

    def set_cnt_total_task(self, value):
        self.__cnt_total_task = value

    def set_successful_tasks(self, value):
        self.__successful_tasks = value

    def set_failed_tasks(self, value):
        self.__failed_tasks = value

    def del_cnt_total_task(self):
        del self.__cnt_total_task

    def del_successful_tasks(self):
        del self.__successful_tasks

    def del_failed_tasks(self):
        del self.__failed_tasks

    cnt_total_task = property(get_cnt_total_task, set_cnt_total_task, del_cnt_total_task, "int : Number of total tasks. Setter is thread")
    successful_tasks = property(get_successful_tasks, set_successful_tasks, del_successful_tasks, "int : Number of succesful tasks.")
    failed_tasks = property(get_failed_tasks, set_failed_tasks, del_failed_tasks, "int : Number of failed tasks.")

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
        progress_str = Util.format_progress(self.get_chunked_cnt(self.get_total_run_tasks()) , self.cnt_total_task)
        time_elapsed = timedelta(seconds=round(time() - self.start_time))
        progress_str = 'Successful: %d, Failed: %d, Total: %s -- Time elapsed: %s' % (self.successful_tasks, self.failed_tasks, progress_str, time_elapsed)
        Util.print_dyn_progress(progress_str)

    ############################################################
    #---Helper
    ############################################################

    def get_chunked_cnt(self, cnt):
        ''' Get correct count then using `chunk`s. Each `chunk` contains `self.tasks_per_chunk` tasks '''
        return min(cnt * self.tasks_per_chunk, self.cnt_total_task)

    def get_total_run_tasks(self):
        ''' Return the total number of tasks that have been run (succesful + failed) '''
        res = self.failed_tasks + self.successful_tasks
        self.__analyzed_cnt_sm.value = res
        return res

    def get_total_run_tasks_sm(self):
        ''' Return the total number of tasks that have been run (succesful + failed) via shared memory '''
        return self.__analyzed_cnt_sm

