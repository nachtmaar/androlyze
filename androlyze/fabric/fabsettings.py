
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Holds fabric settings.
'''

from os.path import join, expanduser

from fabric.state import env

from androlyze import settings as andros
from androlyze.celery.celerysettings import settings as s

############################################################
#---Get settings from config file
############################################################

# set list of workers but don't overwrite run arguments
if not env.hosts:
    env.hosts = s.get_list((andros.SECTION_DEPLOYMENT, andros.KEY_DEPLOYMENT_WORKERS))

CODE_DIR = s[(andros.SECTION_DEPLOYMENT, andros.KEY_DEPLOYMENT_CODE_DIR)]

SCRIPTS_PATH = join(CODE_DIR, s[(andros.SECTION_DEPLOYMENT, andros.KEY_DEPLOYMENT_USERSCRIPTS_PATH)])

GET_CELERY_PROCESS = "ps auxww | grep 'celery worker'"
WORKER_NAME = s[(andros.SECTION_DEPLOYMENT, andros.KEY_DEPLOYMENT_WORKER_NAME)]

############################################################
#---Git stuff
############################################################

REPO_PATH_GIT_URL = s[(andros.SECTION_DEPLOYMENT, andros.KEY_DEPLOYMENT_REPO_PATH_GIT_URL)]
REPO_SUFFIX_HTTP_URL = s[(andros.SECTION_DEPLOYMENT, andros.KEY_DEPLOYMENT_REPO_SUFFIX_HTTP_URL)]

############################################################
#---Not in config
############################################################

# gets user expanded for future use
PID_FILE = expanduser("/tmp/celery/celery.pid")
LOG_FILE = expanduser("/tmp/celery/celery.log")

hosts_str = ', '.join(env.hosts)
DEFAULT_USERNAME = "worker"
