#!/bin/bash

# init configs
echo "initializing Androlyze ..."
docker_init.sh
echo "initializing Androlyze [done]"

# init ssl config
echo "configuring X.509 for Androlyze ..."
worker_ssl_init.sh
echo "configuring X.509 for Androlyze [done]"

# only init necessary submodules to save a bit traffic
echo "getting androguard ..."
git submodule update --init androguard
echo "getting androguard [done]"

# rewrite
echo "rewrite configs ..."
docker_rewrite_configs.py
echo "rewrite configs [done]"

# run worker
echo "running celery worker ..."
docker_run.py