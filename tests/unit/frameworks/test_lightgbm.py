import pytest
from fairing.frameworks import lightgbm
import fairing
import posixpath
from fairing.constants import constants

EXAMPLE_CONFIG = {
    'task': 'train',
    'boosting_type': 'gbdt',
    'objective': 'regression',
    "n_estimators": 10,
    "is_training_metric": True,
    "valid_data": "gs://lightgbm-test/regression.test",
    "train_data": "gs://lightgbm-test/regression.train",
    'verbose': 1,
    "model_output": "gs://lightgbm-test/model.txt"
}

EXMAPLE_CONFIG_FILE_NAME = "/config-file.conf"


def test_context_files_list():
    output_map = lightgbm.generate_context_files(
        EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, False)
    actual = list(output_map.values())
    actual.sort()
    expected = [
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf.original'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'utils.py')
    ]
    expected.sort()
    assert actual == expected


def test_context_files_list_dist():
    output_map = lightgbm.generate_context_files(
        EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, True)
    actual = list(output_map.values())
    actual.sort()
    expected = [
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf.original'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'lightgbm_dist_training_init.py'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'utils.py')
    ]
    expected.sort()
    assert actual == expected


def test_entrypoint_content():
    output_map = lightgbm.generate_context_files(
        EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, False)
    entrypoint_file_in_docker = posixpath.join(constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh')
    entrypoint_file = None
    for k, v in output_map.items():
        if v == entrypoint_file_in_docker:
            entrypoint_file = k
    actual = open(entrypoint_file, "r").read()
    expected = """#!/bin/sh
set -e
gsutil cp gs://lightgbm-test/regression.train {0}/regression.train
gsutil cp gs://lightgbm-test/regression.test {0}/regression.test
echo 'All files are copied!'
lightgbm config={0}/config.conf
gsutil cp {0}/model.txt gs://lightgbm-test/model.txt
""".format(posixpath.realpath(constants.DEFAULT_DEST_PREFIX))
    print(actual)
    assert actual == expected

def test_final_config():
    output_map = lightgbm.generate_context_files(
        EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, False)
    config_file_in_docker = posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf')
    config_file_local = None
    for k, v in output_map.items():
        if v == config_file_in_docker:
            config_file_local = k
    actual = open(config_file_local, "r").read()
    expected = """task=train
boosting_type=gbdt
objective=regression
n_estimators=10
is_training_metric=true
valid_data={0}/regression.test
train_data={0}/regression.train
verbose=1
model_output={0}/model.txt
""".format(posixpath.realpath(constants.DEFAULT_DEST_PREFIX))
    print(actual)
    assert actual == expected