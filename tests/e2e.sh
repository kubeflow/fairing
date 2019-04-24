#!/bin/bash

set -e

gcloud auth activate-service-account --key-file=/secret/gcp-credentials/key.json
gcloud builds submit --config cloudbuild.yaml .
