from __future__ import absolute_import

# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import pickle

from celery import Celery
from kombu.serialization import register

from androlyze.Constants import PROJECT_NAME
from androlyze.celery.celerysettings import settings
from androlyze.settings import *
from androlyze.util import Util
from androlyze.analyze.distributed.tasks.AnalyzeTask import AnalyzeTask
from celery.registry import tasks

# worker has to import androguard too
Util.set_androguard_path(settings)

# set pickle to specific protocol
register('pickle', lambda s: pickle.dumps(s, 2), lambda s: pickle.loads(s),
        content_type='application/x-python-serialize',
        content_encoding='binary')

app = Celery(PROJECT_NAME)

# load config
app.config_from_object(CELERY_CONF)

if __name__ == '__main__':
    app.start()
