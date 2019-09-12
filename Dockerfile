# Copyright 2018 The Kubeflow Authors All rights reserved.
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
FROM alpine:3.7 as builder
RUN apk update && \
    apk add --no-cache curl ca-certificates

ENV DOCKER_CREDENTIAL_GCR_VERSION=1.4.3
RUN curl -LO https://github.com/GoogleCloudPlatform/docker-credential-gcr/releases/download/v${DOCKER_CREDENTIAL_GCR_VERSION}/docker-credential-gcr_linux_amd64-${DOCKER_CREDENTIAL_GCR_VERSION}.tar.gz && \
    tar -zxvf docker-credential-gcr_linux_amd64-${DOCKER_CREDENTIAL_GCR_VERSION}.tar.gz && \
    mv docker-credential-gcr /usr/local/bin/docker-credential-gcr && \
    rm docker-credential-gcr_linux_amd64-${DOCKER_CREDENTIAL_GCR_VERSION}.tar.gz && \
    chmod +x /usr/local/bin/docker-credential-gcr

FROM jupyter/base-notebook:1145fb1198b2
USER jovyan:users
ENV JUPYTER_TOKEN=token
ENV PYTHONPATH /home/jovyan/work/fairing/
RUN mkdir -p /home/jovyan/work/fairing
WORKDIR /home/jovyan/work/fairing/

RUN pip install tensorflow

COPY --from=builder /usr/local/bin/docker-credential-gcr /usr/local/bin/docker-credential-gcr
RUN /usr/local/bin/docker-credential-gcr configure-docker

COPY --chown=jovyan:users requirements.txt /home/jovyan/work/fairing/
RUN pip install --user -r requirements.txt

COPY --chown=jovyan:users integration/ipython_kernel_config.py /home/jovyan/.ipython/profile_default/ipython_kernel_config.py
COPY --chown=jovyan:users containerregistry /home/jovyan/work/fairing/containerregistry

COPY --chown=jovyan:users examples/notebook /home/jovyan/work/fairing/
COPY --chown=jovyan:users kubeflow/fairing /home/jovyan/work/fairing/fairing



