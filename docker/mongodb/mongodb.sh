#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.
#/bin/chown -R mongodb:root /var/log/mongodb/ /var/lib/mongodb

source $ANDROLYZE_UTIL

echo "configuring mongodb ..."
/etc/androlyze_init/mongodb_init.sh
echo "configuring mongodb [done]
"
echo "configuring ssl ..."
/etc/androlyze_init/mongodb_ssl_init.sh
echo "configuring ssl [done]"

echo "starting mongodb ..."
exec /sbin/setuser mongodb\
  /usr/bin/mongod --smallfiles --dbpath /data/db/ \
   --sslWeakCertificateValidation  --sslPEMKeyFile /etc/ssl/private/mongodb.pem --sslOnNormalPorts --sslCAFile $ANDROLYZE_SSL_CA_CERT