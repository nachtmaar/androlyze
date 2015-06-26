
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Fabric helper functions.
'''

from fabric.context_managers import settings
from fabric.operations import run

from androlyze.fabric.fabsettings import *

############################################################
#---Helper methods
############################################################

def cpu_count():
    '''
    Get number of cores.

    Returns
    -------
    int
        Number of cores.
    '''
    return str2int(run(""" python -c "import multiprocessing; print int(multiprocessing.cpu_count())" """))

def str2bool(s):
    '''  Convert str to bool '''
    if isinstance(s, (str, unicode)):
        return s.lower() in ('true', 'yes', '1')
    if isinstance(s, bool):
        return s
    return False

def str2int(s):
    '''  Convert str to int '''
    if isinstance(s, (str, unicode)):
        try:
            return int(s)
        except ValueError:
            pass

# TODO:  pid file /var/run/ ???
def build_celery_opts(concurrency = None, autoscale = True, autoscale_mult = None, worker_name = WORKER_NAME, log_file = LOG_FILE):
    '''
    Build options for "celery worker" command.

    Parameters
    ----------
    concurrency : int
    autoscale : bool, optional (default is True)
    autoscale_mult : int, optional (default is 2)
        concurrency * autoscale_mult is maximum number of processes.
    log_file : str, optional (default is `LOG_FILE`)
        None means no logging to file.
    '''
    if autoscale_mult is None:
        autoscale_mult = 2
    if concurrency is None:
        concurrency = cpu_count()

    CELERY_WORKER_OPTIONS = "%s --app=androlyze.celery.celery -l warn -Q analyze_apk,celery --pidfile=%s -Ofair " % (worker_name, PID_FILE)
    if log_file:
        CELERY_WORKER_OPTIONS = "%s %s" % (CELERY_WORKER_OPTIONS, "--logfile=%s" % log_file)
    if autoscale:
        CELERY_WORKER_OPTIONS += '--autoscale=%s,%s' % (concurrency * int(autoscale_mult), concurrency)
    else:
        CELERY_WORKER_OPTIONS += '--concurrency=%s' % concurrency

    return CELERY_WORKER_OPTIONS

# TODO: VIRTUALENV SUPPORT!
def get_celery_command():
    ''' Check for user version first. Otherwise use system version

    Returns
    -------
    str
        Celery command
    '''
    with settings(warn_only=True):
        if run("test -f ~/.local/bin/celery").failed:
            # system version
            return "celery"

        # user version
        return "~/.local/bin/celery"

def setup_celery_dir():
    ''' Setup the celery directory for logging and pid storage '''
    with settings(warn_only=True):
        # delete old logfile
        run("rm -r %s" % LOG_FILE)
    run("mkdir -p /tmp/celery/")

############################################################
#---Repository
############################################################

def build_git_http_url(user = None, passwd = None):
    ''' If `user` and/or `passwd` given integrate them as authentication into the git http url.
    Otherwise return the normal http url without any credentials included.
    '''
    PROTO_PREFIX = 'http://'

    def build_credentials_str():
        if None not in (user, passwd):
            return    '%s:%s@' % (user, passwd)
        if user is not None:
                return '%s@' % user
        return ""

    return '%s%s%s' % (PROTO_PREFIX, build_credentials_str(), REPO_SUFFIX_HTTP_URL)

