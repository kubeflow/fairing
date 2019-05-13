#!/bin/bash

# Run all the existing unit tests in the repo with pytest

python setup.py install
pip install --upgrade pytest

pushd tests/unit >/dev/null
  pytest
popd
