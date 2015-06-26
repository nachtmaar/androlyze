
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Settings module
'''

import os
from os.path import expanduser, join

from androlyze.log.Log import log
from androlyze.settings.Settings import Settings


############################################################
#---Sections and keys for normal config
############################################################
SECTION_FILE_SYSTEM = "File System"
KEY_FILE_SYSTEM_WRITE_RESULTS_TO_FILE_SYSTEM = "enabled"
KEY_FILE_SYSTEM_RESULT_DIR = "result_dir"

SECTION_DATABASE = "Database"
KEY_DATABASE_IMPORT = "import_database"

SECTION_ANDROGUARD = "Androguard"
KEY_ANDROGUARD_PATH = "androguard_path"

SECTION_APK_DISTRIBUTED_STORAGE = "ApkDistributedStorage"
# use one of the sectio keys as value, e.g. S3Storage
KEY_APK_STORAGE_ENGINE = "storage_engine"

SECTION_S3_STORAGE = "S3Storage"
KEY_S3_STORAGE_AWS_ACCESS_KEY_ID = "aws_access_key_id"
KEY_S3_STORAGE_AWS_SECRET_ACCESS_KEY = "aws_secret_access_key"
KEY_S3_STORAGE_AWS_HOST_URL = "aws_s3_host"
KEY_S3_STORAGE_AWS_APK_BUCKET = "aws_apk_bucket"

SECTION_RESULT_DB = "ResultDatabase"
KEY_RESULT_DB_IP = "mongodb_ip"
KEY_RESULT_DB_PORT = "mongodb_port"
KEY_RESULT_DB_NAME = "mongodb_name"
KEY_RESULT_DB_AUTH_USERNAME = "mongodb_username"
KEY_RESULT_DB_AUTH_PASSWD = "mongodb_passwd"
KEY_RESULT_DB_USE_SSL = "use_ssl"
KEY_RESULT_DB_CA_CERT = "ca_cert"

SECTION_PARALLELIZATION = "Parallelization"
KEY_PARALLELIZATION_CONCURRENCY = "concurrency"
KEY_PARALLELIZATION_THREADED = "threaded"
KEY_PARALLELIZATION_QUEUE_SIZE = "queue_size"

KEY_PARALLELIZATION_MODE = "mode"

# possible values for parallelization mode
PARALLELIZATION_MODE_PARALLEL = "parallel"
PARALLELIZATION_MODE_NON_PARALLEL = "non-parallel"
PARALLELIZATION_MODE_DISTRIBUTED = "distributed"

############################################################
#---Sections and keys for distributed config
############################################################

SECTION_BROKER = "Broker"

# connection url's
KEY_BROKER_URL = "broker_url"
KEY_BROKER_BACKEND_URL = "backend_url"

# broker
KEY_BROKER_USE_SSL = 'use_ssl'
KEY_BROKER_SSL_CA_CERT = 'ca_cert'

# client
KEY_BROKER_SSL_CLIENT_AUTH = 'auth_client'
KEY_BROKER_SSL_CLIENT_KEYFILE = 'client_keyfile'
KEY_BROKER_SSL_CLIENT_CERT = 'client_certfile'

# analysis
SECTION_ANALYSIS = "Analysis"
KEY_ANALYSIS_SCRIPT_HASH_VALIDATION = "script_hash_validation"
KEY_ANALYSIS_SCRIPT_LOAD_RETRY_CNT = "scripts_load_retry_cnt"
KEY_ANALYSIS_RES_DB_OPEN_RETRY_CNT = "result_db_open_retry_cnt"
KEY_ANALYSIS_STORE_RES_RETRY_CNT = "analysis_store_results_retry_cnt"
KEY_ANALYSIS_SOFT_TIME_LIMIT = "soft_time_limit"
KEY_ANALYSIS_HARD_TIME_LIMIT = "hard_time_limit"
KEY_ANALYSIS_TASK_RECOVATION_ENABLED = "task_revocation"

# project deployment etc.
SECTION_DEPLOYMENT = "Deployment"
KEY_DEPLOYMENT_WORKER_NAME = "worker_name"
KEY_DEPLOYMENT_WORKERS = "workers"
KEY_DEPLOYMENT_CODE_DIR = "code_dir"
KEY_DEPLOYMENT_USERSCRIPTS_PATH = "userscripts_path"
KEY_DEPLOYMENT_REPO_PATH_GIT_URL = "repo_path_git_url"
KEY_DEPLOYMENT_REPO_SUFFIX_HTTP_URL = "repo_suffix_http_url"

############################################################
#---Config stuff
############################################################


# home dir for configs
CONFIG_BASEDIR = "conf/"

# default config path
# this is the client specific configuration that lived once in the users home
# to keep it uniform, there is only one config left! 
# CONFIG_PATH = os.path.expanduser("~/.androlyze/config.conf")
CONFIG_PATH = join(CONFIG_BASEDIR, "config.conf")
DISTRIBUTED_CONFIG_PATH = CONFIG_PATH

# the default settings that will be used if no value in config supplied
#DEFAULTS_PATH = "androlyze/settings/defaults/sample.conf"
DEFAULTS_PATH = "androlyze/settings/defaults/config.conf"

# default config file for distributed mode
DISTRIBUTED_DEFAULT_CONFIG_PATH = DEFAULTS_PATH


# has to be package name!
CELERY_CONF = "conf.distributed.celery"

# path for file that holds script paths to scripts that shall be loaded
#SCRIPT_SETTINGS_PATH = '~/.androlyze/script_settings.json'
SCRIPT_SETTINGS_PATH = join(CONFIG_BASEDIR, 'script_settings.json')

SCRIPT_SETTINGS_KEY_SCRIPTS = "scripts"

# key for builtin scripts (paths)
SCRIPT_SETTINGS_SCRIPTS_BUILTIN = "builtin"

# key that selects scripts config to load
SCRIPT_SETTINGS_SCRIPTS_LOAD = "load"

def get_default_scripts():
    ''' Get the default scripts that shall be loaded according to `SCRIPT_SETTINGS_PATH`.
    Returns list<str> (list of paths to script).

    Returns empty list if error occurred.
    '''
    import json
    paths = []
    try:
        config_path = expanduser(SCRIPT_SETTINGS_PATH)
        with open(config_path, "r") as f:
            script_templates = json.load(f)
            # get key that selects the key for script loading
            script_key = script_templates[SCRIPT_SETTINGS_KEY_SCRIPTS][SCRIPT_SETTINGS_SCRIPTS_LOAD]
            paths = script_templates[SCRIPT_SETTINGS_KEY_SCRIPTS][script_key]
    except IOError:
        pass
    except ValueError as e:
        log.warn("Error loading %s due to: %s", config_path, e)
    return paths


singleton = None 
try:
    singleton = Settings( CONFIG_PATH, default_path = DEFAULTS_PATH)
except Exception as e:
    log.error(e)


