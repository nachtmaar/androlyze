
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from copy import deepcopy
from multiprocessing.process import Process

from androlyze.analyze import AnalyzeUtil
from androlyze.analyze.parallel import STOP_SENTINEL
from androlyze.log.Log import clilog, log
from androlyze.model.script import ScriptUtil
from androlyze.storage.exception import StorageException
from androlyze.model.android.apk.FastApk import FastApk

class Worker(Process):
    ''' Worker process that does the actual analysis '''

    def __init__(self, script_list, script_hashes, min_script_needs, work_queue, storage,
                 sm_analyzed_apks, analyzed_apks, storage_results = None):
        '''
        Parameters
        ----------
        script_list: list<type<AndroScript>>
            List of `AndroScript`s references (not instantiated class!)
        script_hashes : list<str>, optional (default is None)
            If given, set the hash for the `AndroScript`s
        min_script_needs : tuple<bool>
            See :py:method:`ScriptUtil.get_maximal_script_options`.
        work_queue : Queue<str>
            Queue with paths to apks which shall be analyzed.
        storage: RedundantStorage
            The storage to store the results.
        sm_analyzed_apks : Value
            Shared memory to add number of analyzed apks.
        analyzed_apks : Queue<FastAPK>
            Holds the analyzed APKs.
        storage_results : Queue<tuple<str, bool>>, optional (default is None)
            Storage results. First component is the id of the entry and the second a boolean indication if the result has been stored in gridfs.

        Raises
        ------
        AndroScriptError
            If an error happened while initializing some `AndroScript`
        '''
        super(Worker, self).__init__()

        # instantiate scripts
        self.androscripts = sorted(ScriptUtil.instantiate_scripts(script_list, script_hashes = script_hashes))

        self.min_script_needs = min_script_needs

        # queues
        self.work_queue = work_queue
        self.analyzed_apks = analyzed_apks
        self.analyzed_apks.cancel_join_thread()
        self.work_queue.cancel_join_thread()

        self.storage = storage

        self.__sm_analyzed_apks = sm_analyzed_apks

        self.__storage_results = storage_results
        self.__storage_results.cancel_join_thread()
        
    def get_storage_results(self):
        return self.__storage_results

    def set_storage_results(self, value):
        self.__storage_results = value

    def del_storage_results(self):
        del self.__storage_results

    def get_androscripts(self):
        return self.__androscripts

    def get_min_script_needs(self):
        return self.__min_script_needs

    def get_work_queue(self):
        return self.__work_queue

    def get_storage(self):
        return self.__storage

    def set_androscripts(self, value):
        self.__androscripts = value

    def set_min_script_needs(self, value):
        self.__min_script_needs = value

    def set_work_queue(self, value):
        self.__work_queue = value

    def set_storage(self, value):
        self.__storage = value

    def del_androscripts(self):
        del self.__androscripts

    def del_min_script_needs(self):
        del self.__min_script_needs

    def del_work_queue(self):
        del self.__work_queue

    def del_storage(self):
        del self.__storage

    androscripts = property(get_androscripts, set_androscripts, del_androscripts, "list<AndroScript> : List of `AndroScript`s")
    min_script_needs = property(get_min_script_needs, set_min_script_needs, del_min_script_needs, " tuple<bool> : See :py:method:`ScriptUtil.get_maximal_script_options`.")
    work_queue = property(get_work_queue, set_work_queue, del_work_queue, "Queue<str> : Queue with paths to apks which shall be analyzed.")
    storage = property(get_storage, set_storage, del_storage, "RedundantStorage : The storage to store the results.")
    storage_results = property(get_storage_results, set_storage_results, del_storage_results, "Queue<tuple<str, bool>> : Storage results. First component is the id of the entry and the second a boolean indication if the result has been stored in gridfs.")

    def add_storage_result(self, storage_result):
        ''' Add `res` to the `storage_results`.

        Parameters
        ----------
        res : tuple<str, bool>
            Storage results. First component is the id of the entry and the second a boolean indication if the result has been stored in gridfs.
        '''
        if self.storage_results is not None:
            self.storage_results.put(storage_result)

    def add_analyzed_apks_sm(self, cnt_analyzed_apks):
        ''' Add `cnt_analyzed_apks` to the shared counter.
        Operation uses an lock! '''
        with self.__sm_analyzed_apks.get_lock():
            self.__sm_analyzed_apks.value += cnt_analyzed_apks

    def analyze_apk(self, eandro_apk):
        ''' Analyze the `eandro_apk` and return the analysis results.

        Parameters
        ----------
        eandro_apk : EAndroApk
            The apk to analyze.

        Returns
        -------
        list<FastApk, AndroScript>
        None
            If error happened.
        '''
        if eandro_apk is not None:

            # analysis
            res = AnalyzeUtil.analyze_apk(eandro_apk, self.androscripts, self.min_script_needs, reset_scripts = True)

            if res is not None:

                fastapk, scripts = res

                # we need to backup the scripts cause they will be reused for a new analysis
                res[1] = deepcopy(scripts)

                clilog.debug("analyzed %s", fastapk.short_description())

                return res

    def __store_results(self, results):
        ''' Store the results and increase the analyzed apks counter.

        Parameters
        ----------
        results : list<FastApk, AndroScript>
        '''
        for res in results:

            # unpack results
            fastapk, script_results = res

            for script in script_results:
                try:
                    storage_result = AnalyzeUtil.store_script_res(self.storage, script, fastapk)
                    self.add_storage_result(storage_result)
                except StorageException as e:
                    log.warn(e)

            self.add_analyzed_apks_sm(1)

    def run(self):
        work_queue = self.work_queue

        try:
            for work in iter(work_queue.get, STOP_SENTINEL):
                try:
                    apk_path, _apk, _ = work
    
                    eandro_apk = AnalyzeUtil.open_apk(apk_path, apk=_apk)
    
                    # do the analysis
                    res = self.analyze_apk(eandro_apk)
    
                    # remember yet analyzed APKs
                    if eandro_apk:
                        self.analyzed_apks.put(FastApk.load_from_eandroapk(eandro_apk))
                    
                    # collect results
                    if res is not None:
                        self.__store_results([res])
                    else:
                        # increment analyzed apks counter
                        self.add_analyzed_apks_sm(1)
                        
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    log.exception(e)
                finally:
                    # signal one task done
                    work_queue.task_done()
    
            # signal sentinel read
            work_queue.task_done()
    
            work_queue.close()
        # be silent
        except KeyboardInterrupt:
            pass
        
