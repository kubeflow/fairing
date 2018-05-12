FROM tensorflow/tensorflow:latest-py3

COPY ./ /opt/metaml
WORKDIR /opt/metaml
RUN python ./setup.py install
