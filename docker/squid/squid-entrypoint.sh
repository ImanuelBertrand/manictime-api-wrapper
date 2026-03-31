#!/bin/sh
set -e

# Re-render the squid config from the template if the conf file is writable
# (it won't be in dev, where squid-dev.conf is mounted read-only).
if [ -w /etc/squid/squid.conf ]; then
    MT_HOSTNAME="${MT_HOSTNAME:-example.invalid}"
    envsubst '${MT_HOSTNAME}' < /etc/squid/squid.conf.template > /etc/squid/squid.conf
fi

exec squid -NYC --foreground
