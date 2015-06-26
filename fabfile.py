
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de""""

import signal

from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.decorators import runs_once
from fabric.operations import run

from androlyze.fabric import FabUtil
from androlyze.fabric.fabsettings import hosts_str, CODE_DIR, WORKER_NAME, \
	PID_FILE, REPO_PATH_GIT_URL, SCRIPTS_PATH, DEFAULT_USERNAME, LOG_FILE
from androlyze.fabric.FabUtil import setup_celery_dir

############################################################
#---Worker comamnds
############################################################

def start_workers(concurrency=None, autoscale = False, autoscale_mult = None):
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
	print "starting workers: %s" % hosts_str
	setup_celery_dir()
	with cd(CODE_DIR):
		run("%s multi start %s" % (FabUtil.get_celery_command(), FabUtil.build_celery_opts(concurrency, autoscale=autoscale, autoscale_mult=autoscale_mult)))


def stop_workers(signal=signal.SIGTERM):
	''' Stop all workers.

	Parameters
	----------
	signal : optional, default is (signal.SIGTERM)

	'''
	print "stopping workers: %s" % hosts_str
	run("%s multi stop %s -%s --pidfile=%s" % (FabUtil.get_celery_command(), WORKER_NAME, signal, PID_FILE))

def restart_workers(concurrency=None, autoscale = False, autoscale_mult = None):
	''' Restart workers on registered hosts with specified concurrency.

	Parameters
	----------
	signal : optional, default is (signal.SIGTERM)
	concurrency : int
	autoscale : bool, optional (default is True)
	autoscale_mult : int, optional (default is None)
		concurrency * autoscale_mult is maximum number of processes.

	See Also
	--------
	http://celery.readthedocs.org/en/latest/reference/celery.bin.multi.html
	'''
	print "restarting workers: %s" % hosts_str
	setup_celery_dir()
	with cd(CODE_DIR):
		run("%s multi restart %s" % (FabUtil.get_celery_command(),
									FabUtil.build_celery_opts(concurrency, autoscale=autoscale, autoscale_mult=autoscale_mult))
		)

############################################################
#---Deployment
############################################################

def deploy_project(user = None, passwd = None, http = True):
	''' If `user` and/or `passwd` given, use them to authenticate when cloning via http.
	If not `http` clone via normal git url.
	'''
	# bool casting
	http = FabUtil.str2bool(http)

	with settings(warn_only=True):
		# only clone if dir not already exists
		if run("test -d %s" % CODE_DIR).failed:
			git_url = FabUtil.build_git_http_url(user, passwd) if http else REPO_PATH_GIT_URL
			run("git clone %s" % git_url)
	# update repository
	with cd(CODE_DIR):
		run("git pull")

def deploy_scripts(scripts_src):
	''' Deploy the scripts on the workers. `scripts_src` is the script folder what shall be synced. '''
	rsync_project(local_dir=scripts_src, remote_dir=SCRIPTS_PATH, exclude = "*.pyc")

def deploy_testing(src_dir = "."):
	''' Deploy the testing code on the workers. Intended for usage where changes have not been comitted (or not to master) '''
	rsync_project(local_dir=src_dir, remote_dir=CODE_DIR, exclude = "*.pyc", extra_opts = '--copy-links --delete-before')

def rm_androlyzelab_dir():
	''' Delete the androlyze folder '''
	run("rm -fr %s" % CODE_DIR)

@runs_once
def initial_worker_setup(username = DEFAULT_USERNAME):
	''' Initial worker setup. Needs root access.
	Add a new user on the workers and install dependencies. '''
	with settings(warn_only = True):
		sudo("adduser %s" % username)
		# gcc and python-dev both optional
		# gcc to compile billiard module
		# otherwise fallback: multiprocessing
		# if not python-dev Python.h not found!!
		sudo("apt-get update && apt-get install python2.7 python-pip gcc python-dev")
		
def install_dependencies():
	''' Set up the workers '''
	with settings(warn_only = True):
		run("pip install --user -r --upgrade docker/worker/requirements.txt")

def install_celery_testing():
	''' Set up the workers '''
	with settings(warn_only = True):
		run("""pip install --user --upgrade https://github.com/celery/celery/zipball/master#egg=celery https://github.com/celery/billiard/zipball/master#egg=billiard https://github.com/celery/py-amqp/zipball/master#egg=amqp https://github.com/celery/kombu/zipball/master#egg=kombu""")


############################################################
#---Process management
############################################################

def list_processes():
	''' List "celery worker" processes '''
	run("ps auxww | grep 'celery worker'")

def cnt_processes():
	''' Cnt "celery worker" processes '''
	run("ps auxww | grep 'celery worker'|wc -l")

def kill_processes():
	''' Kill the workers by sending the kill signal.

	See Also
	--------
	http://celery.readthedocs.org/en/latest/userguide/workers.html#stopping-the-worker
	'''
	with settings(warn_only=True):
		run("""ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9""")
