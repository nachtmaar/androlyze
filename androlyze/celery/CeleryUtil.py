
# encoding: utf-8

from __future__ import absolute_import

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Utility functions for celery.
'''

import sys
from timeit import itertools

from celery import current_app as app, states

from androlyze.analyze.distributed.exception import NetworkError
from androlyze.log.Log import log, clilog
from androlyze.storage.exception import DatabaseLoadException
from androlyze.util import Util


def write_analyze_task_results_to_fs(storage, group_result, chunked = False):
    '''
    Get successful task results and write them to disk if enabled.

    Parameters
    ----------
    storage: RedundantStorage
    group_result : GroupResult
    chunked : bool, optional (default is False)
        If work has been divided into chunks.

    Returns
    -------
    int
        Number of successful tasks
    '''
    if group_result is not None:
        results = get_successful_analyze_task_results(group_result, chunked = chunked)

        # no result writing to disk wanted
        if not storage.fs_storage_disabled():
            clilog.info("Fetching all analysis results for storage ...")
            if results:
                try:
                    storage.fetch_results_from_mongodb(results)
                except DatabaseLoadException as e:
                    log.exception(e)
            return len(results)

    return 0

def get_completed_tasks(group_result, total_cnt, tasks_per_chunk = 1):
    '''
    Get number of completed tasks from `group_result`.

    Parameters
    ----------
    group_result : GroupResult
    total_cnt : int
        Number of total tasks.
    tasks_per_chunk : int, optional (default is 1)
        Number of chunks the work is divided into.
    '''
    # not each chunk has the full number of tasks (last one doesn't)
    return min(total_cnt, group_result.completed_count() * tasks_per_chunk)

def get_successful_analyze_task_results(group_result, chunked = False):
    '''
    Get results for successful tasks from `group_result` (meaning their results) and ignore revoked ones.

    Parameters
    ----------
    group_result : GroupResult
    chunked : bool, optional (default is False)
        If work has been divided into chunks.

    Returns
    -------
    list< tuple<id, gridfs (bool)>>
    '''

    results = []

    def check_n_add(res):
        ''' Check if `res` is ready and has not been revoked etc. '''
        try:
            if res is not None:
                    result = res.get(propagate = False)
                    # if chunked, result is list of multiple tasks -> unpack results
                    if chunked:
                        result = Util.flatten(result)
                    # no result available if e.g. exception raised
                    if result is not None:
                        results.append(result)
        # TaskRevokedError
        except Exception:
            pass

    for res in group_result:
        check_n_add(res)

    # single result is of type list< tuple<id, gridfs (bool)>>
    # so flatten the result!
    return list(itertools.chain(*results))

def exp_backoff(task, _max = 64):
    '''
    Use exponential backoff for task retrying.

    wait_time = 2^1,..., 2^n limit by `_max`.

    Parameters
    ----------
    task : celery.app.task.Task
    _max : int, optional (default is 64)
        Maximum time to use.
    '''
    return min(2 ** task.request.retries, _max)

def get_registered_workers():
    ''' Get the registered celery workers '''
    ping_results = app.control.inspect().ping() or {}
    return ping_results.keys() or ("No workers available/pingable!", )

############################################################
#---Worker and network
############################################################

def get_workers_and_check_network():
    ''' Get the celery workers and check network.

    Returns
    -------
    str
        List of workers as str.

    Raises
    ------
    NetworkError
    '''
    try:
        reg_workers = get_registered_workers()
        return "Registered workers: %s" % ','.join(reg_workers)
    # network
    except IOError as e:
        raise NetworkError(caused_by = e, msg = "Network error or maybe invalid credentials? Have a look at log: /var/log/rabbitmq/<logfile> "), None, sys.exc_info()[2]

############################################################
#---Result fetching/callback
############################################################

def join_native(result_group, timeout=None, propagate=True,
                interval=0.5, callback=None):
    ''' Same as :py:method:`GroupResult.join_native` but delivers task meta too.
    Not just the result!
    '''
    from androlyze.celery import CeleryConstants

    order_index = None if callback else dict(
        (result.id, i) for i, result in enumerate(result_group.results)
    )
    acc = None if callback else [None for _ in range(len(result_group))]
    for task_id, meta in result_group.iter_native(timeout = timeout, interval = interval):
        value = meta
        if propagate and meta[CeleryConstants.CELERY_RESULT_BACKEND_KEY_STATUS] in states.PROPAGATE_STATES:
            raise value
        if callback:
            callback(task_id, value)
        else:
            acc[order_index[task_id]] = value
    return acc
