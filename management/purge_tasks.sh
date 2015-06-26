#!/bin/bash
celery amqp --app=androlyze.celery.celery queue.purge analyze_apk
celery amqp --app=androlyze.celery.celery queue.purge celery


