from __future__ import absolute_import
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
This is the configuration file for celery.

See Also:
---------
http://celery.readthedocs.org/en/latest/configuration.html
'''

from kombu.entity import Queue

from androlyze.celery.CeleryConstants import CELERY_RETRY_INFINITE, \
    get_analyze_task_name
from androlyze.celery.celerysettings import settings as s
from androlyze.settings import SECTION_BROKER, KEY_BROKER_URL, \
    SECTION_ANALYSIS, KEY_ANALYSIS_SOFT_TIME_LIMIT, KEY_ANALYSIS_HARD_TIME_LIMIT

############################################################
#---Broker SSL
# See: www.rabbitmq.com/ssl.html
############################################################

# set broker and result backend url
BROKER_URL = s[(SECTION_BROKER, KEY_BROKER_URL)]

# See: http://docs.celeryproject.org/en/latest/whatsnew-3.1.html?highlight=rpc#new-rpc-result-backend
CELERY_RESULT_BACKEND = 'rpc'

# default is 10
# None or 0 means disable connection pool and init connection every time
BROKER_POOL_LIMIT = 10

# set broker and client ssl options from config file
BROKER_USE_SSL= s.get_celery_broker_ssl_opts()

############################################################
#---Celery message signing
# See: http://celery.readthedocs.org/en/latest/userguide/security.html#message-signing
############################################################

# TODO: FUTURE WORK! CODE-SIGNING!

# from celery.security import disable_untrusted_serializers, setup_security
# CELERY_TASK_SERIALIZER = 'auth'
#
# CELERY_SECURITY_KEY = expanduser('~/androlyze/ssl/client/key.pem')
# CELERY_SECURITY_CERTIFICATE = expanduser('~/androlyze/ssl/client/cert.pem')
# CELERY_SECURITY_CERT_STORE = expanduser('~/androlyze/ssl/certs/*.pem')
#
# setup_security(serializer="pickle")

############################################################
#---Queues
############################################################

# name of our analyze queue
CELERY_QUEUE_ANALYZE_APK = "analyze_apk"

CELERY_DEFAULT_DELIVERY_MODE = 'transient'

# set up queues
CELERY_QUEUES = (

    # default queue
    Queue('celery', routing_key='celery'
          ),

    # analyze queue
    Queue(CELERY_QUEUE_ANALYZE_APK, routing_key=CELERY_QUEUE_ANALYZE_APK
          )
)

# task -> queue routing
CELERY_ROUTES = {get_analyze_task_name(): {'queue': CELERY_QUEUE_ANALYZE_APK}}

# create missing queues
CELERY_CREATE_MISSING_QUEUES = True

############################################################
#---Serialization
############################################################

# disable pickle warning
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERY_TASK_SERIALIZER = 'pickle'

#CELERY_MESSAGE_COMPRESSION = "gzip"

############################################################
#---Worker
############################################################

# can cause deadlocks on unix systems cause fork()
# leads to child processes starting with same memory
CELERYD_FORCE_EXECV = False

# disable rate limits
CELERY_DISABLE_RATE_LIMITS = True

# acknowledge tasks after they have been executed, not before!
CELERY_ACKS_LATE = True

# needs ack late, gets multiplied by concurrency, lowest option
CELERYD_PREFETCH_MULTIPLIER = 1

# get time limits from config
CELERYD_TASK_SOFT_TIME_LIMIT = s.get_int((SECTION_ANALYSIS,KEY_ANALYSIS_SOFT_TIME_LIMIT), default = None)
if CELERYD_TASK_SOFT_TIME_LIMIT is not None:
    CELERYD_TASK_SOFT_TIME_LIMIT *= 60

CELERYD_TASK_TIME_LIMIT = s.get_int((SECTION_ANALYSIS, KEY_ANALYSIS_HARD_TIME_LIMIT), default = None)
if CELERYD_TASK_TIME_LIMIT is not None:
    CELERYD_TASK_TIME_LIMIT *= 60

# reuse processes
CELERYD_MAX_TASKS_PER_CHILD = None

############################################################
#---Task publishing
############################################################

# retry sending task in case of connection failure
CELERY_TASK_PUBLISH_RETRY = True
CELERY_TASK_PUBLISH_RETRY_POLICY = {
    # try until works
    'max_retries': CELERY_RETRY_INFINITE,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
}

############################################################
#---Other
############################################################

CELERY_IMPORT = ["androlyze.analyze.distributed.tasks.AnalyzeTask.AnalyzeTask"]
