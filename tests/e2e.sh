#!/bin/bash

mkdir -p /builder && \
	wget -qO- https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz | tar zxv -C /builder && \
	CLOUDSDK_PYTHON="python3.5" /builder/google-cloud-sdk/install.sh --usage-reporting=false \
		--bash-completion=false \
		--disable-installation-options && \
	rm -rf ~/.config/gcloud
  
export PATH=/builder/google-cloud-sdk/bin/:$PATH
  
pip install pytest pytest-cov papermill
pip install -r examples/prediction/requirements.txt

pip install -e .
python setup.py install

pytest
