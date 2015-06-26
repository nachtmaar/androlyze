
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

class RetryableTask:
    ''' Interface for a retryable celery task '''

    def get_retry_arguments(self):
        ''' Return the argument of the celery task as tuple '''
        raise NotImplementedError