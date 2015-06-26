#!/bin/bash

celery worker --app=androlyze.celery.celery -l info -Q analyze_apk,celery 
#f /tmp/celery/worker.log
