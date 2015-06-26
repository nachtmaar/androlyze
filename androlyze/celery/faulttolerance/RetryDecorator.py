
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys

from androlyze.error.WrapperException import WrapperException
from androlyze.util import Util
from androlyze.celery import CeleryUtil

class RetryDecorator(object):
    ''' Decorator for retrying celery tasks.
    The class that uses it has to implement the interface `RetryableTask`
    '''

    def __init__(self,
                 exception_tuple = (), caused_by_tuple = None,
                 max_retries = None, max_retry_time = 32):
        '''
        Retry task if `max_retries` is not None.
        Use exponential backoff for retry times with maximum time specified by `max_retry_time`.

        Parameters
        ----------
        exception_tuple : tuple<Exception>, optional (default is ())
            The Exceptions for which a retry will be initiated.
        caused_by_tuple: tuple<Exception>, optional (default is None)
            If given, match on `caused_by` of `WrapperException`.
            Only if match succeeds, retry will be initiated!
        max_retries: number, optional (default is None)
            Maximum number of retries. None means try infinite.
        max_retry_time : number, optional (default is 32)
            Maximum time to wait until next retry.
        '''
        self.exception_tuple = exception_tuple
        self.caused_by_tuple = caused_by_tuple
        self.max_retries = max_retries
        self.max_retry_time = max_retry_time

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except self.exception_tuple as e:
                # match on `caused_by`
                if self.caused_by_tuple is None or isinstance(e, WrapperException) and isinstance(e.caused_by, self.caused_by_tuple):

                    # get self reference -> get subclass of RetryableTask
                    cur_task = args[0]

                    # use exponential backoff for retrying
                    retry_time = CeleryUtil.exp_backoff(cur_task, self.max_retry_time)
                    # log error
                    Util.log_will_retry(retry_time, exc = e, what = func.__name__)
                    # retry
                    raise cur_task.retry(args = cur_task.get_retry_arguments(),
                               exc = e,
                               max_retries = self.max_retries,
                               countdown = retry_time
                               )
                # no match on exceptions -> no retry! -> propagate exception
                raise e, None, sys.exc_info()[2]

        return wrapper
