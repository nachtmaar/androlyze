#!/bin/bash

source $ANDROLYZE_UTIL

# create directory for jobs
mkdir -p /var/lib/rabbitmq
chown rabbitmq:rabbitmq -R /var/lib/rabbitmq

# run server
/sbin/setuser rabbitmq /usr/sbin/rabbitmq-server &
rabbitmq_pid=$!

# get credentials from config
regex="broker_url[[:space:]]*=[[:space:]]*amqp:[/][/]([^:]+)[:]([^@]+)[@]"
[[ `cat $CONFIG_PATH` =~ $regex ]]
rabbitmq_user=${BASH_REMATCH[1]}
rabbitmq_pw=${BASH_REMATCH[2]}


if [ -f $CONFIG_PATH ]; then
    if [[ -z `rabbitmqctl list_users 2>/dev/null | grep $rabbitmq_user` ]]; then
        echo "initializing rabbitmq ..."

        # TODO: check if config exists!
        until rabbitmqctl list_users > /dev/null 2>&1; do
            echo -n "."; sleep 1
        done

        # create user
        echo "creating user $rabbitmq_user ..."
        rabbitmqctl add_user $rabbitmq_user $rabbitmq_pw
        rabbitmqctl add_vhost androlyze_vhost
        rabbitmqctl set_permissions -p androlyze_vhost $rabbitmq_user  ".*" ".*" ".*"

        # rabbit mq management plugin
        # echo "enabling rabbit mq management plugin ..."
        # /usr/sbin/rabbitmq-plugins enable rabbitmq_management
        # grant admin permissions
        # TODO: theoretically we need an extra user here!
        rabbitmqctl set_user_tags androlyze administrator

        # we don't want the guest account (administrator)
        rabbitmqctl delete_user guest

        # some debug info
        rabbitmqctl list_users
        rabbitmqctl stop

        kill $rabbitmq_pid
        wait $rabbitmq_pid

        sleep 10

        kill `pgrep rabbitmq-server` 2> /dev/null
        kill `pgrep beam.smp` 2> /dev/null

    else
        echo "user $rabbitmq_user already exists ..."
    fi
else
    echo "config: $CONFIG_PATH does not exist! Is the data container running?"
fi


exit 0