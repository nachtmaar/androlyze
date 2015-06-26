
# encoding: utf-8

from __future__ import absolute_import

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.analyze import AnalyzeUtil
from androlyze.analyze.distributed.exception import ScriptHashValidationError
from androlyze.analyze.exception import AnalyzeError
from androlyze.celery.CeleryConstants import *
from androlyze.celery.celerysettings import *
from androlyze.celery.faulttolerance.RetryDecorator import RetryDecorator
from androlyze.celery.faulttolerance.RetryableTask import RetryableTask
from androlyze.log.Log import log
from androlyze.model.script import ScriptUtil
from androlyze.settings import *
from androlyze.storage.exception import StorageException, DatabaseLoadException, \
    DatabaseOpenError
from androlyze.storage.resultdb import ResultDatabaseStorage
from androlyze.storage.resultdb.ResultDatabaseStorage import CONNECTION_FAIL_ERRORS
from androlyze.util import Util
from billiard.exceptions import SoftTimeLimitExceeded
from celery.app.task import Task
from celery.signals import task_prerun
from gridfs.errors import NoFile
from androlyze.celery import celerysettings

# prefetch pool for apks (only for mongodb as distributed fs)
apk_prefetch_pool = {}

class AnalyzeTask(Task):
    ''' The actual analysis task performed by the celery workers.
    '''

    # retry infinity
    max_retries = None

    # we don't need a traceback for these exceptions
    throws = (NoFile, )

    def __init__(self, *args, **kwargs):
        '''
        A task will be initialized for every process, but not for every task!
        '''
        Task.__init__(self, *args, **kwargs)
        self.__result_database_storage = None
        self.__apk_storage = None
        self.__script_hashes = None
        self.__androscripts = None

        # register signal to prefetch apks
        task_prerun.connect(self.prefetch_apk)

        log.debug("%s init", self)

    def get_apk_storage(self):
        return self.__apk_storage

    def set_apk_storage(self, value):
        self.__apk_storage = value

    def del_apk_storage(self):
        del self.__apk_storage

    def get_result_database_storage(self):
        return self.__result_database_storage

    def get_androscripts(self):
        return self.__androscripts

    def set_result_database_storage(self, value):
        self.__result_database_storage = value

    def set_androscripts(self, value):
        self.__androscripts = value

    def del_result_database_storage(self):
        del self.__result_database_storage

    def del_androscripts(self):
        del self.__androscripts

    def get_script_hashes(self):
        return self.__script_hashes

    def set_script_hashes(self, value):
        self.__script_hashes = value

    def del_script_hashes(self):
        del self.__script_hashes

    script_hashes = property(get_script_hashes, set_script_hashes, del_script_hashes, "list<str> : List of script hashes")
    result_database_storage = property(get_result_database_storage, set_result_database_storage, del_result_database_storage, "ResultDatabaseStorage : Result storage.")
    androscripts = property(get_androscripts, set_androscripts, del_androscripts, " list<AndroScript> : List of `AndroScript`s.")
    apk_storage = property(get_apk_storage, set_apk_storage, del_apk_storage, "ApkCopyInterface : APK Storage")
    
    ############################################################
    #---Signals
    ############################################################

    def prefetch_apk(self, task_id, task, *args, **kwargs):
        ''' Prefetch the `APK`s if mongodb is used as distributed apk storage.
        If the prefetch fails, the task will be retried.
        '''
        try:
            # open db if not already opened
            self.__setup_db()

            args = kwargs["args"]
            _, _, _, apk_zipfile_or_hash, is_hash, fast_apk = args
            # prefetch apk via hash if given
            if is_hash:
                # get apk from the apk storage
                eandro_apk = self.__get_apk_from_storage(apk_zipfile_or_hash, apk = fast_apk)
                if eandro_apk is not None:
                    # store in prefetch pool
                    apk_prefetch_pool[apk_zipfile_or_hash] = eandro_apk
                    log.info("prefetched: %s, size apk cache: %d", eandro_apk.short_description(), len(apk_prefetch_pool))
                    # abort if file not in db!
        except (NoFile, DatabaseOpenError, DatabaseLoadException) as e:
            log.exception(e)

    ############################################################
    #---Setup functions
    ############################################################

    def __setup_db(self):
        ''' Open database if not already done.
        Db will only be set up per process, not for each task!

        Raises
        ------
        StorageException
            Error while opening.
        '''
        if self.result_database_storage is None:
            log.info("setup_db ...")
            
            self.result_database_storage = ResultDatabaseStorage.factory_from_config(settings)
            
    def __setup_apk_storage(self):
        ''' Open APK storage if not already done.
        Storage will only be set up per process, not for each task!

        Raises
        ------
        StorageException
            Error while opening.
        '''
        from androlyze.storage.apk import ApkStorageFactory
        if self.__apk_storage is None:
            self.__apk_storage = ApkStorageFactory.get_apk_storage(settings)

    def __setup_scripts_hash_validation(self, androscripts, script_hashes):
        '''
        Setup scripts.

        Also validate submitted script hashes if script reload is needed!

        Parameters
        ----------
        androscripts : list<str>
            List of package names.
        script_hashes : list<str>
            If given, set the hash for the `AndroScript`s

        Raises
        ------
        AnalyzeError
            If an NoAndroScriptSubclass, IOError or ModuleNotSameClassNameException has been raised.
        ImportError
        ScriptHashValidationError
            If the validation of script hashes fails after reloading scripts from disk.
        '''
        # need tuple to compare
        script_hashes = tuple(script_hashes)

        # import script modules
        script_types = ScriptUtil.import_scripts(androscripts, via_package = True, _reload = True)

        # instantiate scripts and get classes
        self.androscripts = ScriptUtil.instantiate_scripts(script_types,
                                                           # needed for path calculation
                                                           script_paths = [Util.package_name_2_path(s) for s in androscripts])

        actual_hashes = tuple([s.hash for s in self.androscripts])

        if sorted(actual_hashes) != sorted(script_hashes):
            raise ScriptHashValidationError(script_hashes, actual_hashes)


    ############################################################
    #---RetryableTask Interface
    ############################################################

    def get_retry_arguments(self):
        return self.__retry_arguments

    ############################################################
    #---Retryable functions
    ############################################################


    @RetryDecorator(exception_tuple = (ImportError, AnalyzeError),
                    max_retries = CELERY_ANALYSIS_SCRIPT_LOAD_RETRY_CNT,
                    max_retry_time = CELERY_IMPORT_SCRIPTS_ERROR_RETRY_MAX_TIME
                    )
    def __setup_scripts_reuse(self, androscripts, script_hashes):
        '''
        Setup scripts but first try to reuse them.
        This is done by comparing the hashes.

        If they equal -> reuse them!
        Otherwise reload from disk.

        Parameters
        ----------
        androscripts : list<str>
            List of package names.
        script_hashes : list<str>
            If given, set the hash for the `AndroScript`s

        Raises
        ------
        AnalyzeError
            If an NoAndroScriptSubclass, IOError or ModuleNotSameClassNameException has been raised.
        ImportError
        '''

        # need tuple to compare
        script_hashes = tuple(script_hashes)

        script_reload_needed = script_hashes != self.script_hashes

        # script can be reused -> simply reset them
        # stupid comparison cause same scripts in different order are not reused
        # but reusing is rather intended for a reuse in the same analysis (where the order is kept)
        if not script_reload_needed:

            log.info("reusing scripts ... ")
            for s in self.androscripts: s.reset()

        # cannot be reused
        else:
            log.info("reloading scripts cause hashes changed ... ")

            # (re)import script modules
            script_types = ScriptUtil.import_scripts(androscripts, via_package = True, _reload = True)

            # instantiate scripts and get classes
            self.androscripts = ScriptUtil.instantiate_scripts(script_types, script_hashes = script_hashes)

            # set hashes for next comparison
            self.script_hashes = script_hashes


    @RetryDecorator(exception_tuple = (StorageException, ),
                    caused_by_tuple = CONNECTION_FAIL_ERRORS,
                    max_retries = CELERY_ANALYSIS_STORE_RES_RETRY_CNT,
                    max_retry_time = CELERY_DATABASE_STORE_RETRY_MAX_TIME
                    )
    def __store_results(self, fastapk, script_results):
        '''
        Store the results in the database.

        Parameters
        ----------
        fastapk : FastApk
        script_results : list<FastApk, AndroScript>

        Returns
        -------
        list<tuple<str, bool>>
            See :py:method:`.ResultDatabaseStorage.store_result_for_apk`
        '''
        rds = self.result_database_storage
        res = []
        for script in script_results:
            pres = rds.store_result_for_apk(fastapk, script)
            if pres is not None:
                res.append(pres)

        return res

    @RetryDecorator(exception_tuple = (DatabaseLoadException, ),
                    caused_by_tuple = CONNECTION_FAIL_ERRORS,
                    max_retries = CELERY_ANALYSIS_STORE_RES_RETRY_CNT,
                    max_retry_time = CELERY_DATABASE_OPEN_RETRY_MAX_TIME
                    )
    def __open_db(self):
        ''' Open the database. Connection failure -> retry task '''
        self.__setup_db()
        
    @RetryDecorator(exception_tuple = (DatabaseLoadException, ),
                    caused_by_tuple = CONNECTION_FAIL_ERRORS,
                    max_retries = CELERY_ANALYSIS_RES_DB_OPEN_RETRY_CNT,
                    max_retry_time = CELERY_DATABASE_OPEN_RETRY_MAX_TIME
                    )
    def __open_apk_storage(self):
        ''' Open the APK Storage. Connection failure -> retry task '''
        self.__setup_apk_storage()

    @RetryDecorator(exception_tuple = (StorageException, ),
                    caused_by_tuple = CONNECTION_FAIL_ERRORS,
                    max_retries = CELERY_ANALYSIS_RES_DB_OPEN_RETRY_CNT,
                    max_retry_time = CELERY_DATABASE_OPEN_RETRY_MAX_TIME
                    )
    def __get_apk_from_storage_retry(self, apk_id, apk):
        ''' Get the `EAndroApk` from the storage engine. Retry job if connection errors occur.

        Parameters
        ----------
        apk_id : str
            The id of the apk
        apk : FastApk
        '''
        return self.apk_storage.get_apk(apk_id, apk = apk)

    ############################################################
    #---other
    ############################################################

    def __get_apk_from_storage(self, apk_id, apk):
        ''' Get the `EAndroApk` from the storage engine (MongoDB or S3)

        Parameters
        ----------
        apk_id : str
            The id of the apk
        apk : FastApk
        '''
        if self.apk_storage is not None:
            return self.apk_storage.get_apk(apk_id, apk = apk)
        

    ############################################################
    #---Actual Analysis
    ############################################################

    def run(self, androscripts, min_script_needs, script_hashes, apk_zipfile_or_hash, is_hash = True, fast_apk = None):
        '''
        Do the analysis on the apk with the given scripts.

        Parameters
        ----------
        androscripts : list<str>
            List of package names.
        script_hashes : list<str>
            If given, set the hash for the `AndroScript`s
        min_script_needs : tuple<bool>
            See :py:method:`ScriptUtil.get_maximal_script_options`.
        apk_zipfile_or_hash : str
            The raw contents of the .apk file or the hash (sha256).
            The raw content of the .apk file (zipfile) or the hash of it (id in db).
        is_hash : bool, optional (default is True)
            Determines if `apk_zipfile_or_hash` is a hash (id).
        fast_apk : FastApk, optional (default is None)
            Holds the meta infos for the apk.

        Returns
        -------
        tuple<tuple<str, bool>>
            First component is the id of the entry
            and the second a boolean indication if the result has been stored in gridfs.
        ()
            If an error occurred.
        '''
        try:
            # method retry_arguments
            self.__retry_arguments = androscripts, min_script_needs, script_hashes, apk_zipfile_or_hash, is_hash, fast_apk
            eandro_apk = None
            do_script_hash_validation = settings.script_hash_validation_enabled()

            # open database/apk storage if not already done
            # reschedule job if connection/open error
            self.__open_db()
            self.__open_apk_storage()

            # setup scripts
            if do_script_hash_validation:
                # validate sent hashes with local script hashes
                self.__setup_scripts_hash_validation(androscripts, script_hashes)
            else:
                # reuse if possible
                self.__setup_scripts_reuse(androscripts, script_hashes)

            # open apk
            if not is_hash:
                log.info("opening apk via raw data ... ")
                eandro_apk = AnalyzeUtil.open_apk(apk_or_path = apk_zipfile_or_hash, apk = fast_apk, raw = True)
            else:
                # get apk from prefetched apk pool
                eandro_apk = apk_prefetch_pool.get(apk_zipfile_or_hash, None)
                # could not prefetch
                if eandro_apk is None:
                    eandro_apk = self.__get_apk_from_storage_retry(apk_zipfile_or_hash, apk = fast_apk)

            # if None, could not be opened and error has been logged
            if eandro_apk is not None:
                result = AnalyzeUtil.analyze_apk(eandro_apk, self.androscripts, min_script_needs, propagate_error = False, reset_scripts = not do_script_hash_validation)

                if result is not None:
                    fastapk, script_results = result

                    log.info("analyzed %s", fastapk.short_description())
                    storage_results = self.__store_results(fastapk, script_results)
                    # can be None if errorr occurred
                    if storage_results:
                        return tuple(storage_results)

            return ()
        except SoftTimeLimitExceeded:
            log.warn("Task %s exceeded it's soft time limit!", self)
            raise
        except ScriptHashValidationError:
            raise
        finally:
            # delete from pool -> we don't need it anymore in the pool
            if is_hash and apk_zipfile_or_hash in apk_prefetch_pool:
                del apk_prefetch_pool[apk_zipfile_or_hash]
