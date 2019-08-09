#!/bin/bash

# Kick off the full integration test on cloud build.
# TODO(abhishek): move this integration test over to argo workflow

set -e

pip3 install -U tornado

sysctl fs.inotify.max_user_instances
sysctl fs.inotify.max_user_instances=524288

gcloud auth activate-service-account --key-file=/secret/gcp-credentials/key.json
gcloud builds submit --config cloudbuild.yaml .
