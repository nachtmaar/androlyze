#!/bin/bash

source $ANDROLYZE_UTIL

CONFIG_DEST_DIR="conf"
CONF_FILE="config.conf"
SSH_DIR="$WORKER_HOME/.ssh"

SCRIPT_SETTINGS="script_settings.json"

mkdir -p $CONFIG_DEST_DIR

for config in $CONF_FILE $SCRIPT_SETTINGS
do
	conf_dest_file="$CONFIG_DEST_DIR/$config"
	conf_src_file="$CONFIG_DIR/$config"
    if [ ! -f $conf_dest_file ] ; then
        if [ -f $conf_src_file ]; then
            echo "copying $conf_src_file to $conf_dest_file"
            cp "$conf_src_file" "$conf_dest_file"
            chown worker $conf_dest_file
            chmod 600 $conf_dest_file
        else
            echo "$conf_src_file not existing!"
        fi
    else
        echo "config $conf_dest_file already exists!"
    fi
done