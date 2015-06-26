
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.settings import *
from androlyze.settings.Settings import Settings

# global celery settings instance
settings = Settings(DISTRIBUTED_CONFIG_PATH, default_path = DISTRIBUTED_DEFAULT_CONFIG_PATH)

############################################################
#---Values from celery config
############################################################

CELERY_ANALYSIS_RES_DB_OPEN_RETRY_CNT = settings.get_int((SECTION_ANALYSIS, KEY_ANALYSIS_RES_DB_OPEN_RETRY_CNT), default = None)
CELERY_ANALYSIS_STORE_RES_RETRY_CNT = settings.get_int((SECTION_ANALYSIS, KEY_ANALYSIS_STORE_RES_RETRY_CNT), default = None)
CELERY_ANALYSIS_SCRIPT_LOAD_RETRY_CNT = settings.get_int((SECTION_ANALYSIS, KEY_ANALYSIS_SCRIPT_LOAD_RETRY_CNT), default = None)

CELERY_TASK_REVOCATION_ENABLED = settings.__getitem__((SECTION_ANALYSIS, KEY_ANALYSIS_TASK_RECOVATION_ENABLED), default = True)
