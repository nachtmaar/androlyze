
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from multiprocessing import JoinableQueue as Queue
from multiprocessing import cpu_count
import os
import signal

from androlyze.analyze import AnalyzeUtil
from androlyze.analyze.BaseAnalyzer import BaseAnalyzer
from androlyze.analyze.parallel import STOP_SENTINEL
from androlyze.analyze.parallel.AnalysisStatsView import AnalysisStatsView
from androlyze.analyze.parallel.Worker import Worker
from androlyze.log.Log import log
from androlyze.util import Util


class ParallelAnalyzer(BaseAnalyzer):
    ''' Parallel analyzer which uses the `multiprocessing` module. '''

    def __init__(self,
                 storage, script_list, script_hashes, min_script_needs, apks_or_paths,
                 concurrency = None):
        '''
        See :py:method`.BaseAnalyzer.__init__` for details on the first attributes.

        Other Parameters
        ----------------
        concurrency : int, optional (default is number of cpu cores)
            Number of workers to spawn.
        '''
        super(ParallelAnalyzer, self).__init__(storage, script_list, script_hashes, min_script_needs, apks_or_paths)

        # parallelization parameters
        if concurrency is None:
            concurrency = cpu_count()

        self.__concurrency = concurrency

        log.info("concurrency: %s", self.concurrency)
        log.info("Using processes")

        # parallel stuff, concerning processes
        self.__work_queue = Queue()
        self.__work_queue.cancel_join_thread()
        self.__workers = []
        
        self.__analyzed_apks = Queue()

    def get_analyzed_apks(self):
        return self.__analyzed_apks

    def set_analyzed_apks(self, value):
        self.__analyzed_apks = value

    def del_analyzed_apks(self):
        del self.__analyzed_apks

    def get_work_queue(self):
        return self.__work_queue

    def get_concurrency(self):
        return self.__concurrency

    def get_workers(self):
        return self.__workers

    def set_workers(self, value):
        self.__workers = value

    def del_workers(self):
        del self.__workers

    analyzed_apks = property(get_analyzed_apks, set_analyzed_apks, del_analyzed_apks, "Queue<FastAPK> : Yet analyzed APKs")
    concurrency = property(get_concurrency, None, None, "int : Number of workers to spawn.")
    workers = property(get_workers, set_workers, del_workers, "list<Worker> : List of workers.")
    work_queue = property(get_work_queue, None, None, "Queue<str> : Queue with paths to apks which shall be analyzed.")

    def _analyze(self):
        ''' See doc of :py:method:BaseAnalyzer.analyze`. '''
        try:
            work_queue = self.work_queue

            # create worker pool
            log.debug("starting %s workers ...", self.concurrency)
            for _ in range(self.concurrency):
                p = Worker(self.script_list, self.script_hashes, self.min_script_needs,
                                                 work_queue, self.storage,
                                                 self.cnt_analyzed_apks, self.analyzed_apks, self.storage_results)
                self.workers.append(p)
                p.daemon = True

            # start workers
            for p in self.workers:
                p.start()

            # queue has size limit -> start workers first then enqueue items
            log.info("Loading apk paths into work queue ...")
            for apk_stuff in AnalyzeUtil.apk_gen(self.apks_or_paths):
                # task is apk with all scripts
                work_queue.put(apk_stuff)

            for _ in range(self.concurrency):
                # signal end-of-work
                work_queue.put(STOP_SENTINEL)

            # progress view for cli
            av = AnalysisStatsView(self.cnt_analyzed_apks, self._cnt_apks, self.analyzed_apks)
            av.daemon = True
            av.start()
            
            # block until workers finished
            work_queue.join()
            av.terminate()
            log.debug("joined on work queue ...")

            return self.cnt_analyzed_apks.value

        # try hot shutdown first
        except KeyboardInterrupt:
            log.warn("Hot shutdown ... ")
            try:
                log.warn("clearing work queue ... ")
                Util.clear_queue(work_queue)
                log.warn("cleared work queue ... ")
                
                for _ in range(self.concurrency):
                    # signal end-of-work
                    work_queue.put(STOP_SENTINEL)
                    
                for worker in self.workers:
                    worker.join()
                log.warn("waited for all workers ... ")

                return self.cnt_analyzed_apks.value

            # if user really wants make a cold shutdown -> kill processes
            except KeyboardInterrupt:
                log.warn("Cold shutdown ... ")
                log.warn("Hard shutdown wanted! Killing all workers!")

                # kill processes via SIGINT -> send CTRL-C
                for w in self.workers:
                    try:
                        os.kill(w.pid, signal.SIGINT)
                    except:
                        pass

                return self.cnt_analyzed_apks.value
