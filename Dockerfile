FROM tensorflow/tensorflow

COPY ./ /opt/metaml
WORKDIR /opt/metaml
RUN python ./setup.py install
