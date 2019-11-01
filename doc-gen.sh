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

set -o errexit
set -o nounset
set -o pipefail

PROJECT="Fairing"
VERSION="V0.6.1"
CURRENT_PATH=`pwd`
#TMP_PATH=`mktemp -d`
TMP_PATH=$CURRENT_PATH/docs_tmp_$(date +%s)
mkdir -p $TMP_PATH

# Install the pre-requisites
pip install -U Sphinx sphinx-rtd-theme sphinx-markdown-builder
pip install -r requirements.txt

cd ${TMP_PATH}
# Generate required files for a Sphinx project.
sphinx-quickstart --sep -p ${PROJECT} -a 'Kubeflow Author' -r ${VERSION} -l en ${TMP_PATH} --ext-autodoc

# Update source/conf.py to setup path and imprt sphinx_rtd_theme
sed -i.sedbak '/# -- Path setup/a \
import sphinx_rtd_theme\
import os\
import sys\
sys.path.insert(0, os.path.abspath("../.."))\
' source/conf.py

sed -i.sedbak s/"html_theme = 'alabaster'"/"html_theme = 'sphinx_rtd_theme'"/ source/conf.py
sed -i.sedbak '/html_theme =/a \
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]\
' source/conf.py

# Generate source files
sphinx-apidoc -o ./source ${CURRENT_PATH}/kubeflow/

# Generate HTML files
make html

# Generate Markdown files
make markdown

# Copy the useful files to docs
mkdir -p ${CURRENT_PATH}/docs/
cp -rf ${TMP_PATH}/build/html ${CURRENT_PATH}/docs/
cp -rf ${TMP_PATH}/build/markdown ${CURRENT_PATH}/docs/

# Clean up temp files
cd ${CURRENT_PATH}
rm -rf ${TMP_PATH}
