#!/usr/bin/env bash
set -e

export FLASK_ENV=production

# Run the app with gunicorn binding to the port Render provides
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
