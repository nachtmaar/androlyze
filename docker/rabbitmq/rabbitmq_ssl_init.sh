#!/bin/bash

source $ANDROLYZE_UTIL

# copy certificate and key
cp $ANDROLYZE_SSL_SERVER_KEY /etc/ssl/private/
cp $ANDROLYZE_SSL_SERVER_CERT $ANDROLYZE_SSL_CA_CERT /etc/ssl/certs/

# keep private key private
chmod 600 /etc/ssl/private/androlyze_server.key
chown rabbitmq:rabbitmq -R /etc/ssl/private/androlyze_server.key

cat << EOF >  /etc/rabbitmq/rabbitmq.config
[
  {rabbit, [
     {tcp_listeners, []},
     {ssl_listeners, [5671]},
     {ssl_options, [{cacertfile,"/etc/ssl/certs/androlyze_ca.pem"},
                    {certfile,"/etc/ssl/certs/androlyze_server.crt"},
                    {keyfile,"/etc/ssl/private/androlyze_server.key"},
                    {verify,verify_peer},
                    {fail_if_no_peer_cert,true}]}
   ]},

  {rabbitmq_management,
    [{listener, [{port,     15672},
                 {ssl,      true},
                 {ssl_opts, [{cacertfile, "/etc/ssl/certs/androlyze_ca.pem"},
                             {certfile,   "/etc/ssl/certs/androlyze_server.crt"},
                             {keyfile,    "/etc/ssl/private/androlyze_server.key"}]}
                 ]}
  ]}

].
EOF