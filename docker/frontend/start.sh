#!/bin/bash

# init configs
./docker_init.sh
# rewrite
./docker_rewrite_configs.py
# loop forever
tail -f docker_run.py