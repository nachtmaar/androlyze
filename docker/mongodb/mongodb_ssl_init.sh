#!/bin/bash

source $ANDROLYZE_UTIL

# copy certificate and key
cat $ANDROLYZE_SSL_SERVER_CERT $ANDROLYZE_SSL_SERVER_KEY > /etc/ssl/private/mongodb.pem
cp $ANDROLYZE_SSL_CA_CERT /etc/ssl/certs/

# keep private key private
chmod 600 /etc/ssl/private/mongodb.pem
chown mongodb:mongodb -R /etc/ssl/private/mongodb.pem

