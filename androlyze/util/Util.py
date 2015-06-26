
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Utility module
'''

from Queue import Empty
import itertools
from os.path import splitext
import re
import sys
import time
import traceback

from androlyze.log.Log import log


def sha256(data):
    '''
    Calculate the sha256 hash

    Parameters
    ----------
    data: object

    Returns
    -------
    str
        sha256 as hexstring
    '''
    import hashlib

    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()

def cs_classnames(class_list, sort = True):
    ''' Returns a comma separated str build from the name attribute '''
    class_names = [c.__name__ for c in class_list]
    if sort:
        class_names = sorted(class_names)
    return ', '.join(class_names)

def filter_not_none(sequence):
    return filter(lambda x: x is not None, sequence)

def get_fst_not_none(sequence):
    ''' Get the first object that is not None.
    Returns None if nothing found '''
    res = filter_not_none(sequence)
    if res:
        return res[0]
    return None

def format_exception(exc_info_obj, as_string = True):
    '''
    Format the exception infos to a string

    Parameters
    ----------
    exc_info_obj :  (type, value, traceback)
        An object like sys.exc_info() returns
    as_string : bool
        If true, return the formatted exception as string, not list<str>

    Returns
    -------
    str
    '''
    res = traceback.format_exception(*exc_info_obj)
    if as_string:
        res = ''.join(res)
    return res

############################################################
#---Datetime conversions
############################################################

def utc2local(utc_datetime):
    ''' Convert `datetime` object in utc to local time zone.

    Parameters
    ----------
    utc_datetime : datetime
        Datetime object with utc timezone

    Examples
    --------
    >>> from datetime import datetime
    ... print utc2local(datetime.utcnow())

    Returns
    -------
    datetime
        Datetime object with local timezone
    '''
    import calendar
    from datetime import datetime

    # get integer timestamp to avoid precision lost
    # but we lose microseconds due to the timetuple()
    timestamp = calendar.timegm(utc_datetime.timetuple())
    local_datetime = datetime.fromtimestamp(timestamp)
    # get micro seconds back
    local_datetime.replace(microsecond=utc_datetime.microsecond)
    return local_datetime

############################################################
#---Conversion ISO-8601 <-> Datetime
############################################################

def iso8601_to_datetime(iso_dt):
    ''' Convert a date represented as ISO-8601 string to a `datetime ` object (utc).

    Examples
    --------
    >>> from datetime import datetime
    ... iso8601_to_datetime(datetime.utcnow().isoformat())
    '''
    from dateutil import parser
    return parser.parse(iso_dt)

def datetime_to_iso8601(dt):
    ''' Convert a `datetime` object to a ISO-8601 string.

    Examples
    --------
    >>> from datetime import datetime
    ... datetime_to_iso8601(datetime.utcnow())
    '''
    return dt.isoformat()

############################################################
#---Other
############################################################

def transform_key(key, from_mapping, to_mapping):
    '''
    Find the `key` in `from_mapping` and return the value of `to_mapping` at this index.

    Parameters
    ----------
    key : str
    from_mapping : list<str>
    to_mapping : list<str>

    Returns
    -------
    appropriate value in the `to_mapping`
    '''
    try:
        idx = from_mapping.index(key)
        return to_mapping[idx]
    except ValueError:
        return None

def timeit(func, *args, **kwargs):
    ''' Returns the execution time in seconds of the func.

    Returns
    -------
    int
        Execution time if no result value
    tuple<int, object>
        If the `func` has a return value, a tuple will be returned.
        1. arg time, 2. arg result value'''
    start = time.time()
    res = func(*args, **kwargs)
    end = time.time()
    duration = end - start

    if res is None:
        return duration

    return (duration, res)

def set_androguard_path(settings):
    ''' Set the path to androguard from read from `settings` if not already in python path!

    Parameters
    ----------
    settings : Settings
    '''

    # check if path already set
    try:
        import androguard
        return
    except ImportError:
        pass

    from androlyze.settings import SECTION_ANDROGUARD, KEY_ANDROGUARD_PATH

    ANDROGUARD_PATH = settings[(SECTION_ANDROGUARD, KEY_ANDROGUARD_PATH)]
    # set androguard location before importing any androguard stuff
    sys.path.append(ANDROGUARD_PATH)
    log.info('appending "%s" to sys.path', ANDROGUARD_PATH)

############################################################
#---Logging
############################################################

def print_dyn_progress(progress_str):
    ''' Print progress on stdout.

    Parameters
    ----------
    progress_str : str
    '''
    sys.stdout.write("\r%s" % progress_str)
    sys.stdout.flush()

def log_will_retry(secs, exc = None, what = ''):
    '''
    Parameters
    ----------
    secs : int
        Retry in `secs` seconds.
    exc: Exception, optional (default is None)
        Exception to log
    what : str, optional (default is '')
        What to try again.
    '''
    if exc is not None:
        log.exception(exc)
    log.warn("Trying %s again in %ss", what, secs)

############################################################
#---Lists
############################################################

def flatten(l):
    ''' Flatten the iterable `l` '''
    return list(itertools.chain(*l))

############################################################
#---Progress
############################################################

def format_progress(cur_cnt, total_cnt):
    ''' Format progress and return it as str.

    Parameters
    ----------
    cur_cnt : int
    total_cnt : int
    '''
    progress_percentage = calc_progress(cur_cnt, total_cnt)
    progress_percentage_str = "%.2f" % progress_percentage

    return "%s/%s (%s %%)" % (cur_cnt, total_cnt, progress_percentage_str)

def calc_progress(cur_cnt, total_cnt):
    ''' Calculate progress and return it as float.

    Parameters
    ----------
    cur_cnt : int
    total_cnt : int
    '''
    progress_percentage = 0
    if total_cnt != 0:
        progress_percentage = cur_cnt * 100.0 / total_cnt
    return progress_percentage

############################################################
#---Import
############################################################

def path_2_package_name(path):
    ''' Convert path to package name '''
    return re.sub("/+", ".", splitext(path)[0])

def package_name_2_path(package_name):
    ''' Convert package name to path'''
    return re.sub("\.+", "/", package_name) + ".py"

def module_names_from_class(classes):
    ''' Get module names from instantiated `classes` '''
    return map(lambda s: s.__module__, classes)

############################################################
#---Itertools
############################################################

def count_iterable_n_clone(iterable):
    '''
    Parameters
    ----------
    iterable: iterable structure


    Returtns
    --------
    iterable, int
        The first component is the iterable structure.
        List if `iterable` was list, otherwise `itertools.tee`
        Second is the count of elements.
    '''
    is_list = isinstance(iterable, list)
    orig, copy = itertools.tee(iterable)
    if is_list:
        orig = list(orig)

    return orig, len(list(copy))

def queue_to_list(queue):
    ''' Get all elements from the `queue` and return them as list.

    Parameters
    ----------
    qeueue: multiprocessing.Queue
    '''
    res = []
    while True:
        try:
            r = queue.get_nowait()
            res.append(r)
        except Empty:
            break
    return res

def split_n_uniform_distri(l, n = 10):
    ''' Split the list `l` into `n` sublists and try to fill each sublist with nearly the same number of elements.
    So achieve an uniform distribution in all sublists.

    Examples
    --------
    >>> split_n_uniform_distri(range(11))
    [[0, 10], [1], [2], [3], [4], [5], [6], [7], [8], [9]]
    '''
    return [l[i::n] for i in range(0, n)]

def clear_queue(queue):
    ''' Clear the queue by removing all elements (without blocking)

    Parameters
    ----------
    queue : multiprocessing.Queue or Queue

    Warning
    -------
    If the queue is a `JoinableQueue` it's not joinable any more!
    '''
    try:
        while True:
            queue.get_nowait()
    except Empty:
        pass