#!/bin/bash

# Copyright 2019 The Kubeflow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This shell script is used to test xgboost notebook.
set -o errexit
set -o nounset
set -o pipefail

# Upgrade to python 3.6 since the kfp need higher python version.
apt-get update -yqq
apt-get install -yqq --no-install-recommends software-properties-common
add-apt-repository -y ppa:jonathonf/python-3.6
apt-get update -yqq
apt-get install -yqq --no-install-recommends  python3.6 python3-pip
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.5 1
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 2

# Install docker service.
apt-get remove docker docker-engine docker.io containerd runc
apt-get update -yqq
apt-get install -yqq apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
apt-get update -yqq
apt-get install -yqq docker-ce docker-ce-cli containerd.io

# Install the required pacakges for executing notebook.
python3 -m pip install --upgrade pip
pip3 install -U papermill ipykernel tornado
#pip3 install git+git://github.com/kubeflow/fairing.git@c6c075dece72135f5883abfe2a296894d74a2367
#pip3 install tornado>=6.0.3

# Run testing.
python3 execute_notebook.py
