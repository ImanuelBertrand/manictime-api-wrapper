#!/bin/bash
set -e

export FLASK_APP="wsgi.py"

CONFIG_MODE=${FLASK_ENV:-production}
echo "Running in $CONFIG_MODE mode..."

exec python -m gunicorn --bind 0.0.0.0:8000 --timeout 60 --access-logfile - \
    --limit-request-line 4094 --limit-request-fields 50 --limit-request-field_size 4094 \
    "wsgi:app"
