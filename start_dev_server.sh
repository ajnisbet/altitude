#!/usr/bin/env bash
xdg-open 'http://localhost:8087' & \
python /opt/google-cloud-sdk/platform/google_appengine/dev_appserver.py "${BASH_SOURCE%/*}/app.yaml" \
 --port 8087 \
 --admin_port 8007 \
 --storage_path /tmp/altitude-203221