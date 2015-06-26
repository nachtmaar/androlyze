
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Holds some constants/settings related to celery.
'''

from androlyze.settings import *

############################################################
#---Max retry wait time
############################################################

# maximum wait time for database open
CELERY_DATABASE_OPEN_RETRY_MAX_TIME = 32

# maximum wait time for import script error
CELERY_IMPORT_SCRIPTS_ERROR_RETRY_MAX_TIME = 0

# maximum wait time for database storage
CELERY_DATABASE_STORE_RETRY_MAX_TIME = 120

############################################################
#---Result backend constants
# used to get information from callback handlers
############################################################

CELERY_RESULT_BACKEND_KEY_RESULT = "result"
CELERY_RESULT_BACKEND_KEY_TRACEBACK = "traceback"
CELERY_RESULT_BACKEND_KEY_STATUS = "status"

############################################################
#---Other
############################################################

# value for retrying until success
CELERY_RETRY_INFINITE = None

def get_analyze_task_name():
    from androlyze.analyze.distributed.tasks.AnalyzeTask import AnalyzeTask
    return AnalyzeTask.name
