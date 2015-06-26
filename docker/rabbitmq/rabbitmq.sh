#!/bin/sh
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

echo "rabbitmq setup ..."
/etc/androlyze_init/rabbitmq_init.sh
echo "rabbitmq setup [done]"

# enable ssl
echo "rabbitmq ssl init ..."
/etc/androlyze_init/rabbitmq_ssl_init.sh
echo "rabbitmq ssl init [done]"

# redirect logs to docker
echo "redirecting logs to stdout/stderr ..."
exec /sbin/setuser rabbitmq tail -f /var/log/rabbitmq/startup_err > /dev/stderr 2>/dev/null &
for logf in "/var/log/rabbitmq/startup_log" "/var/log/rabbitmq/rabbit@localhost.log" "/var/log/rabbitmq/rabbit@localhost-sasl.log"; do
    exec /sbin/setuser rabbitmq tail -f $logf > /dev/stdout 2>/dev/null &
done

# start rabbitmq
echo "rabbitmq start ..."
exec /sbin/setuser rabbitmq /usr/sbin/rabbitmq-server
