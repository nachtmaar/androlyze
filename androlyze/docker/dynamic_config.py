
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import os
import re

from androlyze.docker.util import run
from androlyze.log.Log import clilog
from androlyze.settings import *

# environment variable names
## docker
RABBITMQ_DOCKER_CONN = "RABBITMQ_PORT"
MONGODB_DOCKER_CONN = "MONGODB_PORT"
## kubernetes    
RABBITMQ_HOST = 'RABBITMQ_SERVICE_SERVICE_HOST'
RABBITMQ_PORT = 'RABBITMQ_SERVICE_SERVICE_PORT'
MONGODB_HOST = 'MONGODB_SERVICE_SERVICE_HOST'
MONGODB_PORT = 'MONGODB_SERVICE_SERVICE_PORT'

envs_kubernetes = [RABBITMQ_HOST, RABBITMQ_PORT, MONGODB_HOST, MONGODB_PORT]
envs_docker = [RABBITMQ_DOCKER_CONN, MONGODB_DOCKER_CONN]

def get_rabbitmq_conn_info():
    ''' Get the ip and port of the rabbitmq service '''
    rabbitmq_conn = os.environ.get(RABBITMQ_DOCKER_CONN)
    # provided by docker
    if rabbitmq_conn:
        return re.search("tcp://(.*):(.*)", rabbitmq_conn).groups()
    # kubernetes
    else:
        return os.environ.get(RABBITMQ_HOST), os.environ.get(RABBITMQ_PORT)
    
def get_mongodb_conn_info():
    ''' Get the ip and port of the rabbitmq service '''
    mongodb_conn = os.environ.get(MONGODB_DOCKER_CONN)
    # provided by docker
    if mongodb_conn:
        return re.search("tcp://(.*):(.*)", mongodb_conn).groups()
    # kubernetes
    else:
        return os.environ.get(MONGODB_HOST), os.environ.get(MONGODB_PORT)

def rewrite_configs():
    clilog.info("using environment variables for service discovery (kubernetes): %s", ', '.join(envs_kubernetes))
    clilog.info("using environment variables for service discovery (docker): %s", ', '.join(envs_docker))
    clilog.info("rabbitmq: host: %s, port: %s", *get_rabbitmq_conn_info())
    clilog.info("mongodb: host: %s, port: %s", *get_mongodb_conn_info())

    def rewrite_config_key(key, value, config_path = CONFIG_PATH):
        key = key.strip()
        value = value.strip()
        return run(r""" sed -i.bak "s/\(%s[ ]*=[ ]*\).*/\1%s/g" %s """ % (key, value, config_path))
        
    def rewrite_amqp(user = r"\2", pw = r"\3", host = r"\4", port = r"\5", vhost = r"\6", config_path = CONFIG_PATH):
        any(
            run(r""" sed -i.bak "s/\(%s[ ]*=[ ]*amqp:[/][/]\)\(.*\)[:]\(.*\)[@]\(.*\)[:]\(.*\)[/]\(.*\)/\1%s:%s@%s:%s\/%s/g" %s """ % (key, user, pw, host, port, vhost, config_path))
            for key in [KEY_BROKER_URL, KEY_BROKER_BACKEND_URL]
        )
            
    mongodb_ip, mongodb_port = get_mongodb_conn_info()
    if mongodb_ip is not None:
        rewrite_config_key(KEY_RESULT_DB_IP, mongodb_ip)
    
    if mongodb_port is not None:
        rewrite_config_key(KEY_RESULT_DB_PORT, mongodb_port)
        
    rabbitmq_ip, rabbitmq_port = get_rabbitmq_conn_info()
    rewrite_amqp(host = rabbitmq_ip, port = rabbitmq_port)


