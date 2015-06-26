
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys
from threading import Lock
from time import time

from celery import states, task
from celery.canvas import group
from celery.result import GroupResult
from celery.signals import before_task_publish, after_task_publish

# init celery
import androlyze.celery.celery

from androlyze.analyze import AnalyzeUtil
from androlyze.analyze.AnalyzeUtil import apk_gen
from androlyze.analyze.BaseAnalyzer import BaseAnalyzer
from androlyze.analyze.distributed.AnalysisStatsView import AnalysisStatsView
from androlyze.analyze.distributed.exception import NetworkError
from androlyze.celery import CeleryUtil, CeleryConstants, celerysettings
from androlyze.log.Log import log, clilog
from androlyze.celery.TaskCollection import TaskCollection
from androlyze.storage.exception import DatabaseOpenError, \
    DatabaseLoadException
from androlyze.util import Util
from celery.registry import tasks


class DistributedAnalyzer(BaseAnalyzer):
    ''' Distributed analyzer which uses celery.
    The analysis of each apk is seen as a single task and gets done by a worker which reads from an asynchronous message queue.
    '''

    def __init__(self, *args, **kwargs):
        '''
        See :py:method`.BaseAnalyzer.__init__` for details.

        Parameters
        ----------
        serialize_apks : bool, optional (default is True)
            If true, serialize .apk .
            Otherwise id (hash) of the apk will be send and fetched by the worker from the result db.
            Be sure to import the apks to the result db first!
        '''
        serialize_apks = kwargs.get("serialize_apks", True)

        super(DistributedAnalyzer, self).__init__(*args, **kwargs)

        # list(apk_path, _apk, is_apk)
        self.__apks = list(AnalyzeUtil.apk_gen(self.apks_or_paths))

        # result group
        self.group_result = None

        # serialize .apk data
        self.__serialize_apks = serialize_apks
        if serialize_apks:
            clilog.info("Will serialize .apk data!")
        else:
            clilog.info("Will send id of apks!")

        self.analyze_stats_view = None

        # stats view for cli
        self.analyze_stats_view = AnalysisStatsView(self._cnt_apks)
        self.analyze_stats_view.daemon = True

        # the `TaskCollection` for the analysis tasks
        self.task_collection = TaskCollection(self._cnt_apks)

        # register celery signals
        self.register_signals()

        self.lock = Lock()

    def get_lock(self):
        return self.__lock

    def set_lock(self, value):
        self.__lock = value

    def del_lock(self):
        del self.__lock

    def get_analyze_stats_view(self):
        return self.__analyze_stats_view

    def set_analyze_stats_view(self, value):
        self.__analyze_stats_view = value

    def del_analyze_stats_view(self):
        del self.__analyze_stats_view

    def get_serialize_apks(self):
        return self.__serialize_apks

    def get_apks(self):
        return self.__apks

    def set_apks(self, value):
        self.__apks = value

    def set_cnt_apks(self, value):
        self.__cnt_apks = value

    def del_apks(self):
        del self.__apks

    def del_cnt_apks(self):
        del self.__cnt_apks

    def get_group_result(self):
        return self.__group_result

    def set_group_result(self, value):
        self.__group_result = value

    def del_group_result(self):
        del self.__group_result

    group_result = property(get_group_result, set_group_result, del_group_result, "GroupResult : The result collection object.")
    apks = property(get_apks, set_apks, del_apks, "list<tuple<str, Apk, bool>> : Path to .apk, instance of `Apk`, bool what determines if current element of apks_or_paths is an `Apk`")
    serialize_apks = property(get_serialize_apks, None, None, "bool : If true, serialize .apk. Otherwise id (hash) of the apk will be send and fetched by the worker from the result db.")
    analyze_stats_view = property(get_analyze_stats_view, set_analyze_stats_view, del_analyze_stats_view, "AnalysisStatsView : Thread showing current analysis progress.")
    lock = property(get_lock, set_lock, del_lock, "Lock")

    ############################################################
    #---Signals
    ############################################################

    def register_signals(self):
        ''' Register celery signals for task publishing '''
        # register signals
        before_task_publish.connect(self.before_task_publish_action, sender = CeleryConstants.get_analyze_task_name())
        after_task_publish.connect(self.after_task_publish_action, sender = CeleryConstants.get_analyze_task_name())

    ############################################################
    #---Analysis progress display
    ############################################################

    def stop_analysis_view(self):
        ''' Stop displaying the analysis progress and return the number of successful + failed tasks. '''
        if self.analyze_stats_view is not None:
            analyzed_cnt = None
            # terminate by using event
            if self.analyze_stats_view.isAlive():
                analyzed_cnt = self.analyze_stats_view.get_total_run_tasks()
                self.analyze_stats_view.terminate()
                # wait for analysis view
                self.analyze_stats_view.join()
            return analyzed_cnt
        return 0

    ############################################################
    #---Shared memory stats
    ############################################################

    def get_cnt_analyzed_apks(self):
        ''' Return the number of analyzed apks '''
        return self.analyze_stats_view.get_total_run_tasks_sm()

    def get_published_tasks_sm(self):
        ''' Return the number of published tasks '''
        return self.task_collection.send_tasks

    cnt_analyzed_apks = property(get_cnt_analyzed_apks, lambda s: s.set_cnt_analyzed_apks, lambda s: s.del_cnt_analyzed_apks, "Value<int> : Shared memory integer showing the count of already analyzed apks")

    ############################################################
    #---Task arguments generators
    ############################################################

    def send_id_args_generator(self, apk_gen):
        ''' Generator over arguments for sending of apk id.

        Parameters
        ----------
        generator<tuple<object, bool>>
            Generator over zip files or ids.
            Second component of tuples indicates that the generator is other the id's
            rather than over the zip files.
            See :py:method:`.AnalyzeUtil.apk_id_or_raw_data_gen` to get such a generator.
        '''
        # get package names from initialized scripts
        script_packages = Util.module_names_from_class(self.script_list)

        for apk_zipfile_or_hash, is_id, fastapk in apk_gen:
            yield script_packages, self.min_script_needs, self.script_hashes, apk_zipfile_or_hash, is_id, fastapk

    def send_apk_args_generator(self, apk_gen):
        ''' Generator over arguments for sending APKs.

        Parameters
        ----------
        generator<tuple<object, bool>>
            Generator over zip files or ids.
            Second component of tuples indicates that the generator is other the id's
            rather than over the zip files.
            See :py:method:`.AnalyzeUtil.apk_id_or_raw_data_gen` to get such a generator.
        '''
        # get package names from initialized scripts
        script_packages = Util.module_names_from_class(self.script_list)

        for apk_zipfile_or_hash, is_id, fast_apk in apk_gen:
            yield script_packages, self.min_script_needs, self.script_hashes, apk_zipfile_or_hash, is_id, fast_apk

    ############################################################
    #---Analysis
    ############################################################

    def _analyze(self):
        ''' See doc of :py:method:`.BaseAnalyzer.analyze`. '''

        # try to get registered workers
        # it network fails at this point -> stop analysis
        try:
            clilog.info(CeleryUtil.get_workers_and_check_network())
        except NetworkError as e:
            log.critical(e)
            return 0

        # storage objects
        storage = self.storage

        clilog.info("Number of apks to analyze: %d", self._cnt_apks)

        try:
            # get analyze task
            analyze_task = tasks[CeleryConstants.get_analyze_task_name()]

            # create storage
            storage.create_or_open_sub_storages()

            # send tasks
            start = time()

            # apk generator over .apk or apk hashes
            apk_gen = AnalyzeUtil.apk_id_or_raw_data_gen(self.apks, force_raw_data = self.serialize_apks)

            clilog.info("Task publishing progress:")

            # send and serialize .apks
            # if analysis via path serialize them!
            if self.serialize_apks:
                log.info("sending .apks to message broker")
                self.group_result = group_result = GroupResult(results = [])

                for args in self.send_apk_args_generator(apk_gen):
                    task = analyze_task.delay(*args)
                    group_result.add(task)

            # send only apk id and let fetch via mongodb
            else:
                log.info("sending ids of apks")

                task_group = group((analyze_task.s(*args) for args in self.send_id_args_generator(apk_gen)))

                # publish tasks
                self.group_result = task_group()

            log.info("sending took %ss", (time() - start))
            sys.stderr.write("\nAnalysis progress:\n")

            # start showing analysis progress
            self.analyze_stats_view.start()

            # wait for results
            log.debug("joining on ResultGroup ... ")

            # setup callback
            callback_func = self.get_callback_func(self.success_handler, self.error_handler)
            CeleryUtil.join_native(self.group_result, propagate = False, callback = callback_func)

            clilog.info("\nanalysis done ... ")
            log.info("distributed analysis took %ss", (time() - start))

            return self.stop_analysis_view()
        except DatabaseOpenError as e:
            log.critical(e)
            return 0

        except (KeyboardInterrupt, Exception) as e:
            if not isinstance(e, KeyboardInterrupt):
                log.exception(e)
            log.warn("Interrupting distributed analysis ... Please wait a moment!")
            log.warn("revoking tasks on all workers ...")

            if celerysettings.CELERY_TASK_REVOCATION_ENABLED:
                # revoke tasks
                if self.group_result is None:
                    # revoke via task ids
                    log.debug("revoking while publishing tasks ...")

                    self.task_collection.revoke_all(terminate = True, signal = 'SIGKILL')
                else:
                    # revoke via GroupResult if yet available/created
                    # first available after all tasks have been send
                    self.group_result.revoke(terminate = True, signal = 'SIGKILL')
                log.warn("revoked tasks and killed workers ...")

            #return number of analyzed apks
            return self.stop_analysis_view()


    ############################################################
    #---Callbacks
    ############################################################

    def error_handler(self, task_id, error_msg, state, traceback = None):
        ''' Handler for a failed task.

        Parameters
        ----------
        task_id : str
            UUID of task.
        error_msg : str
            Error message.
        state : See `state` module
            State of the task.
        traceback : str
            The traceback if error occurred.
        '''
        # progress view does not print a newline, so do it here
        sys.stdout.write("\n")

        # log error msg
        log.error(str(error_msg))

        # print traceback if available
        if traceback:
            log.error(traceback)

    def success_handler(self, task_id, result):
        ''' Handler for a successful task.
        Fetches the result from the result database and stores it in the file system. '''
        if result is not None:
            # keep ids of mongodb entries
            # result may hold multiple results
            for res in result:
                self.add_storage_result(res)

            # store analysis results
            # doesn't raise a DatabaseLoadException due to wait_for_db
            self.storage.fetch_results_from_mongodb(result, wait_for_db = True)

    def get_callback_func(self, handle_success, handle_error = None):
        '''
        Callback function for task finish.
        Store results and display progress

        Parameters
        ----------
        handle_success : func
            Function for the success of a task.
            E.g. handle_success(task_id, result) with type:
            handle_success: str -> object -> object
        handle_error : func, optional (default is None)
            Function that gets the task id and error message for a task that failed.
            E.g. handle_error(task_id, error_msg, state, traceback = None)
            with type handle_error: str -> str -> str -> str -> object.

        Returns
        -------
        function<str, object>
        '''

        def callback(task_id, result_dict):
            '''
            Parameters
            ----------
            task_id : str
                UUID of task.
            result_dict : dict
                Dictionary holding the meta infos about the task as well as the result.
                See `CeleryConstants.CELERY_RESULT_BACKEND_*` for some available keys.
            '''
            log.debug("Task %s finished", task_id)

            result = result_dict[CeleryConstants.CELERY_RESULT_BACKEND_KEY_RESULT]
            traceback = result_dict[CeleryConstants.CELERY_RESULT_BACKEND_KEY_TRACEBACK]
            state = result_dict[CeleryConstants.CELERY_RESULT_BACKEND_KEY_STATUS]

            task_failed = state in states.EXCEPTION_STATES

            # show exceptions
            if task_failed:

                # handle error
                if handle_error is not None:
                    handle_error(task_id, result, state, traceback)

                # we need locking here because operation is not atomic
                with self.lock:
                    self.analyze_stats_view.failed_tasks += 1

            else:
                if handle_success is not None:
                    handle_success(task_id, result)

                # we need locking here because operation is not atomic
                with self.lock:
                    self.analyze_stats_view.successful_tasks += 1

        return callback

    ############################################################
    #---Signals
    ############################################################

    def before_task_publish_action(self, *args, **kwargs):
        ''' Collect task ids before they get published '''
        task_id = kwargs["body"]["id"]
        log.debug("will publish task %s", task_id)
        self.task_collection.task_ids.append(task_id)

    def after_task_publish_action(self, exchange=None, body=None, routing_key = None, signal = None, sender = None,
                                  # take unknown keywords for newer APIs
                                   **kwargs):
        '''
        Inform user about published tasks.

        Function will be executed on the task sender after the task has been published.

        Parameters
        ----------
        exchange : str
        body : dict, optional (default is None)
            The task message body, see Task Messages for a reference of possible fields that can be defined.
        routing_key : str
        signal : signal.Signal
        sender : str

        See Also
        --------
        http://celery.readthedocs.org/en/latest/userguide/signals.html#after-task-publish
        '''
        self.task_collection.inc_send_tasks()

        task_id = body["id"]
        Util.print_dyn_progress("Send tasks: %d, current task id: %s, queue: %s" % (self.task_collection.send_tasks.value, task_id, routing_key))

    ############################################################
    #---Other
    ############################################################

    def all_tasks_published(self):
        ''' Check if all tasks have been published '''
        return self.task_collection.all_tasks_published()

