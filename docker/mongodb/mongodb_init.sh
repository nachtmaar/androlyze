#!/bin/bash

source $ANDROLYZE_UTIL

chown -R mongodb:mongodb /data/db/
/sbin/setuser mongodb mongod --smallfiles --dbpath /data/db/ --auth &

mongodb_pid=$!

if [ -f $CONFIG_PATH ]; then

    echo "initializing mongodb ..."

    mongodb_username=$(config_value_for_key mongodb_username)
    mongodb_passwd=$(config_value_for_key mongodb_passwd)

    until "exit" | mongo > /dev/null 2>&1; do
        echo -n "."; sleep 1
    done

    echo "use admin
    db.addUser( { user: '$mongodb_username',
                  pwd: '$mongodb_passwd',
                  roles: [ 'readWriteAnyDatabase'] } )

    #db.addUser( { user: 'useradmin',
    #              pwd: '$mongodb_passwd',
    #              roles: [ 'userAdminAnyDatabase'] } )

    " | mongo

    echo "use admin
    db.auth('$mongodb_username', '$mongodb_passwd')
    " | mongo

    kill $mongodb_pid
    wait $mongodb_pid

else
    echo "config: $CONFIG_PATH does not exist! Is the data container running?"
fi

exit 0