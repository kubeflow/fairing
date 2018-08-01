FROM tensorflow/tensorflow:latest-py3

COPY ./ /opt/fairing
WORKDIR /opt/fairing
RUN python ./setup.py install
