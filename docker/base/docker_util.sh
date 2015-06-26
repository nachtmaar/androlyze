#!/bin/bash

CONFIG_DIR="/etc/androlyze/"
CONFIG_PATH=/etc/androlyze/config.conf

# X.509 stuff
ANDROLYZE_SSL_SERVER_CERT="/etc/androlyze/androlyze_server.crt"
ANDROLYZE_SSL_SERVER_KEY="/etc/androlyze/androlyze_server.key"
ANDROLYZE_SSL_CA_CERT="/etc/androlyze/androlyze_ca.pem"

ANDROLYZE_SSL_CLIENT_CERT="/etc/androlyze/androlyze_client.crt"
ANDROLYZE_SSL_CLIENT_KEY="/etc/androlyze/androlyze_client.key"
ANDROLYZE_SSL_CLIENT_CA_CERT="/etc/androlyze/androlyze_ca.pem"

# Get value from the config file. First argument is the key in the config.
config_value_for_key() {
    regex="$1[[:space:]]*=[[:space:]]*([^[:space:]]+)"
    [[ `cat $CONFIG_PATH` =~ $regex ]]
    echo ${BASH_REMATCH[1]}
}


WORKER_CONFIG_PATH="conf/config.conf"
WORKER_HOME="/home/worker/"
WORKER_SSL_HOME="/home/worker/androlyze/conf/distributed/ssl/"