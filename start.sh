#!/usr/bin/env bash
set -e

export FLASK_ENV=production

waitress-serve --port=5000 app:app
