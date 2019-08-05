#!/bin/bash

# Kick off the full integration test on cloud build.
# TODO(abhishek): move this integration test over to argo workflow

set -e

pip3 install -U tornado

gcloud auth activate-service-account --key-file=/secret/gcp-credentials/key.json
gcloud builds submit --config cloudbuild.yaml .
