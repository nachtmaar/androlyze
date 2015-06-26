
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from multiprocessing import Value, Queue, RLock
from androlyze.util import Util

class BaseAnalyzer(object):
    '''
    Base analyzer which offers functions for analyzing an apk file with the help of androguard.
    It can use scripts that derive from `AndroScript`.
    '''

    def __init__(self,
                 storage, script_list, script_hashes, min_script_needs, apks_or_paths, cnt_apks = None, storage_results = None, **kwargs):
        '''
        Use the `import_scripts` method to get a list<type<AndroScript>> from a list of absolute paths (to the scripts).

        Parameters
        ----------
        storage: RedundantStorage
            The storage to store the results.
        script_list: list<type<AndroScript>>
            List of `AndroScript`s references (not instantiated class!)
        script_hashes : list<str>, optional (default is None)
            If given, set the hash for the `AndroScript`s
        min_script_needs : tuple<bool>
            See :py:method:`ScriptUtil.get_maximal_script_options`.
        apks_or_paths: iterable<str> or list<Apk>, optional (default is [])
            List of `Apk` or paths to the apks which shall be analyzed with the given scripts
            If you analyze from paths the `import_date` is not set!
        cnt_apks : int, optional
            Total number of apks to analyze.
            If not given, calculate it.
        storage_results : Queue<tuple<str, bool>>, optional (default is Queue)
            Storage results. First component is the id of the entry
            and the second a boolean indication if the result has been stored in gridfs.
            Will be created if not supplied!

        Raises
        ------
        AndroScriptError
            If an error happened while initializing some `AndroScript`.
        '''
        super(BaseAnalyzer, self).__init__()
        if apks_or_paths is None:
            apks_or_paths = []

        self.__storage = storage
        self.__script_list = script_list
        self.__script_hashes = script_hashes
        self.__min_script_needs = min_script_needs

        if cnt_apks is None:
            # calculate cnt apks if not given
            apks_or_paths, cnt_apks = Util.count_iterable_n_clone(apks_or_paths)

        self.__apks_or_paths = apks_or_paths
        self._cnt_apks = cnt_apks

        # shared memory
        self._cnt_analyzed_apks = Value('i', 0, lock = RLock())
        if storage_results is None:
            storage_results = Queue()
        self._storage_results = storage_results
        
    def get_storage(self):
        return self.__storage

    def get_script_list(self):
        return self.__script_list

    def get_script_hashes(self):
        return self.__script_hashes

    def get_apks_or_paths(self):
        return self.__apks_or_paths

    def get_min_script_needs(self):
        return self.__min_script_needs

    def set_storage(self, value):
        self.__storage = value

    def set_script_list(self, value):
        self.__script_list = value

    def set_script_hashes(self, value):
        self.__script_hashes = value

    def set_apks_or_paths(self, value):
        self.__apks_or_paths = value

    def set_min_script_needs(self, value):
        self.__min_script_needs = value

    def del_storage(self):
        del self.__storage

    def del_script_list(self):
        del self.__script_list

    def del_script_hashes(self):
        del self.__script_hashes

    def del_apks_or_paths(self):
        del self.__apks_or_paths

    def del_min_script_needs(self):
        del self.__min_script_needs

    storage = property(get_storage, set_storage, del_storage, "StorageInterface : The storage to store the results.")
    script_list = property(get_script_list, set_script_list, del_script_list, "list<type<AndroScript>> : List of `AndroScript`s references (not instantiated class!)")
    script_hashes = property(get_script_hashes, set_script_hashes, del_script_hashes, "list<str>, optional (default is None) : If given, set the hash for the `AndroScript`s")
    apks_or_paths = property(get_apks_or_paths, set_apks_or_paths, del_apks_or_paths, "iterable<str> or list<Apk>, optional (default is []) : List of `Apk` or paths to the apks which shall be analyzed with the given scripts. If you analyze from paths the `import_date` is not set!")
    min_script_needs = property(get_min_script_needs, set_min_script_needs, del_min_script_needs, "tuple<bool> : See :py:method:`ScriptUtil.get_maximal_script_options`.")

    def analyze(self, *args, **kwargs):
        '''
        Start the analysis and store the results in the predefined place.

        Returns
        -------
        int
            Number of analyzed apks
        '''
        res = self._analyze(*args, **kwargs)
        if self.storage_results:
            self.storage_results.close()
        return res

    def _analyze(self):
        ''' Implement this method in the Analyzer subclass.

        Returns
        -------
        int
            Number of analyzed apks
        '''
        raise NotImplementedError

    ############################################################
    #---Shared memory
    ############################################################

    def get_cnt_analyzed_apks(self):
        return self._cnt_analyzed_apks

    def set_cnt_analyzed_apks(self, value):
        '''
        Parameters
        ----------
        value : int
        '''
        self._cnt_analyzed_apks.value = value

    def del_cnt_analyzed_apks(self):
        del self._cnt_analyzed_apks

    cnt_analyzed_apks = property(get_cnt_analyzed_apks, set_cnt_analyzed_apks, del_cnt_analyzed_apks, "Value<int> : Shared memory integer showing the count of already analyzed apks")

    def get_total_cnt(self):
        ''' Return the total number of apks to analyze.

        Returns
        -------
        multiprocessing.Value
            Shared memory count.
        '''
        return Value('i', self._cnt_apks)

    def get_storage_results(self):
        return self._storage_results

    def set_storage_results(self, value):
        self._storage_results = value

    def del_storage_results(self):
        del self._storage_results

    def add_storage_result(self, res):
        ''' Add `res` to the `storage_results`.

        Parameters
        ----------
        res : tuple<str, bool>
            Storage results. First component is the id of the entry and the second a boolean indication if the result has been stored in gridfs.
        '''
        self.storage_results.put(res)

    storage_results = property(get_storage_results, set_storage_results, del_storage_results, "Queue<tuple<str, bool>> : Storage results. First component is the id of the entry and the second a boolean indication if the result has been stored in gridfs.")

    ############################################################
    #---Helper
    ############################################################

    def is_non_parallel_analyzer(self):
        ''' Check if `BaseAnalyzer` is `Analyzer` '''
        from androlyze.analyze.Analyzer import Analyzer
        return isinstance(self, Analyzer)

    def is_parallel_analyzer(self):
        ''' Check if `BaseAnalyzer` is `ParallelAnalyzer` '''
        from androlyze.analyze.parallel.ParallelAnalyzer import ParallelAnalyzer
        return isinstance(self, ParallelAnalyzer)

    def is_distributed_analyzer(self):
        ''' Check if `BaseAnalyzer` is `DistributedAnalyzer` '''
        try:
            from androlyze.analyze.distributed.DistributedAnalyzer import DistributedAnalyzer
            # celery maybe not installed -> return False
        except ImportError:
            return False
        return isinstance(self, DistributedAnalyzer)
