#!/bin/bash

# Kick off the full integration test on cloud build.
# TODO(abhishek): move this integration test over to argo workflow

set -e

gcloud auth activate-service-account --key-file=/secret/gcp-credentials/key.json
gcloud builds submit --config cloudbuild.yaml .
