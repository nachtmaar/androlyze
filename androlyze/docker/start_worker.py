
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from multiprocessing import cpu_count
import os

from androlyze.docker.util import run
from androlyze.fabric import FabUtil
from androlyze.fabric.fabsettings import LOG_FILE

def start_workers(concurrency=cpu_count(), autoscale = False, autoscale_mult = None):
    ''' Start workers on registered hosts with specified concurrency.
    
    Parameters
    ----------
    concurrency : int
    autoscale : bool, optional (default is True)
    autoscale_mult : int, optional (default is 2)
        concurrency * autoscale_mult is maximum number of processes.
    
    See Also
    --------
    http://celery.readthedocs.org/en/latest/reference/celery.bin.multi.html
    '''
    run("rm -r %s" % LOG_FILE)
    run("mkdir -p /tmp/celery/")    
    run("%s worker %s" % (get_celery_command(), FabUtil.build_celery_opts(concurrency, worker_name = "", autoscale=autoscale, autoscale_mult=autoscale_mult,
                                                                          # log to stdout
                                                                         log_file=None)))
    
def get_celery_command():
    ''' Check for user version first. Otherwise use system version
    
    Returns
    -------
    str
        Celery command
    '''
    if os.system("test -f ~/.local/bin/celery") != 0:
        # system version
        return "celery"
    
    # user version
    return "~/.local/bin/celery"
