#!/bin/bash

python setup.py install
pip install --upgrade pytest

pushd tests/unit >/dev/null
  pytest
popd
