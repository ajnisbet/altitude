#!/usr/bin/env bash

python /opt/google-cloud-sdk/platform/google_appengine/dev_appserver.py "${BASH_SOURCE%/*}/app.yaml" \
 --port 8082 \
 --admin_port 8002 \
 --storage_path /tmp/delta-z-203221