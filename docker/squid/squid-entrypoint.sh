#!/bin/sh
set -e

# Re-render the squid config from the template if the conf file is writable
# (it won't be in dev, where squid-dev.conf is mounted read-only).
if [ -w /etc/squid/squid.conf ]; then
    MT_HOSTNAME="${MT_HOSTNAME:-example.invalid}"
    MT_PORT="${MT_PORT:-80}"
    envsubst '${MT_HOSTNAME} ${MT_PORT}' < /etc/squid/squid.conf.template > /etc/squid/squid.conf
fi

exec squid -NYC --foreground
