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
FROM golang:1.10.1 as builder

ENV DOCKER_CREDENTIAL_GCR_VERSION=1.4.3
RUN curl -LO https://github.com/GoogleCloudPlatform/docker-credential-gcr/releases/download/v${DOCKER_CREDENTIAL_GCR_VERSION}/docker-credential-gcr_linux_amd64-${DOCKER_CREDENTIAL_GCR_VERSION}.tar.gz && \
    tar -zxvf docker-credential-gcr_linux_amd64-${DOCKER_CREDENTIAL_GCR_VERSION}.tar.gz && \
    mv docker-credential-gcr /usr/bin/docker-credential-gcr && \
    rm docker-credential-gcr_linux_amd64-${DOCKER_CREDENTIAL_GCR_VERSION}.tar.gz && \
    chmod +x /usr/bin/docker-credential-gcr && \
    docker-credential-gcr configure-docker

WORKDIR /go/src/github.com/kubeflow/fairing/kubeflow
COPY vendor ./vendor
COPY Makefile .

COPY cmd ./cmd
COPY pkg ./pkg

RUN make install

FROM jupyter/base-notebook:1145fb1198b2
ENV JUPYTER_TOKEN=token
COPY --chown=jovyan:users config/ipython_kernel_config.py /home/jovyan/.ipython/profile_default/ipython_kernel_config.py
COPY --from=builder --chown=jovyan:users /root/.docker/config.json /home/jovyan/.docker/config.json
COPY --from=builder /usr/bin/docker-credential-gcr /usr/bin/docker-credential-gcr

COPY --from=builder /go/bin/fairing /usr/bin/fairing
COPY --chown=jovyan:users fairing-py  /home/jovyan/work/lib/
