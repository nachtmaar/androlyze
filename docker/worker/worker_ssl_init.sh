#!/bin/bash

source $ANDROLYZE_UTIL

# copy certificate and key
mkdir -p $WORKER_SSL_HOME
cp $ANDROLYZE_SSL_CLIENT_CERT $ANDROLYZE_SSL_CLIENT_KEY $ANDROLYZE_SSL_CLIENT_CA_CERT $WORKER_SSL_HOME

# keep private key private
chown worker:worker -R $WORKER_SSL_HOME
chmod 700 -R $WORKER_SSL_HOME
