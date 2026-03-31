#!/bin/bash
set -e

export FLASK_APP="wsgi.py"

CONFIG_MODE=${FLASK_ENV:-production}
echo "Running in $CONFIG_MODE mode..."

exec python -m gunicorn --bind 0.0.0.0:8000 "wsgi:app"
