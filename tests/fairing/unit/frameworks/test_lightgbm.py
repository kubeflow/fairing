import pytest
from kubeflow.fairing.frameworks import lightgbm
from kubeflow import fairing #pylint:disable=unused-import
import posixpath
from kubeflow.fairing.constants import constants
from unittest.mock import patch

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
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists'):
        output_map = lightgbm.generate_context_files(
            EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, 1)
    actual = list(output_map.values())
    actual.sort()
    expected = [
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf.original'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'utils.py')
    ]
    expected.sort()
    assert expected == actual


def test_context_files_list_dist():
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists'):
        output_map = lightgbm.generate_context_files(
            EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, 2)
    actual = list(output_map.values())
    actual.sort()
    expected = [
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf.original'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'config.conf'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX,
                       'lightgbm_dist_training_init.py'),
        posixpath.join(constants.DEFAULT_DEST_PREFIX, 'utils.py')
    ]
    expected.sort()
    assert expected == actual


def test_entrypoint_content():
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists'):
        output_map = lightgbm.generate_context_files(
            EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, 1)
    entrypoint_file_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh')
    entrypoint_file = None
    for k, v in output_map.items():
        if v == entrypoint_file_in_docker:
            entrypoint_file = k
    actual = open(entrypoint_file, "r").read()
    expected = """#!/bin/sh
set -e
gsutil cp -r gs://lightgbm-test/regression.train.weight {0}/regression.train.weight
gsutil cp -r gs://lightgbm-test/regression.train {0}/regression.train
gsutil cp -r gs://lightgbm-test/regression.test {0}/regression.test
echo 'All files are copied!'
lightgbm config={0}/config.conf
gsutil cp -r {0}/model.txt gs://lightgbm-test/model.txt
""".format(posixpath.realpath(constants.DEFAULT_DEST_PREFIX))
    print(actual)
    assert expected == actual


def test_final_config():
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists'):
        output_map = lightgbm.generate_context_files(
            EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, 1)
    config_file_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, 'config.conf')
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
    assert expected == actual


def test_input_file_not_found():
    with pytest.raises(RuntimeError) as excinfo:
        with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists', new=lambda x, y: False):
            _ = lightgbm.generate_context_files(
                EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, 1)
    err_msg = str(excinfo.value)
    assert "Remote file " in err_msg and "does't exist" in err_msg


def test_entrypoint_content_no_weight_file():
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists',
               new=lambda bucket, path: not path.endswith(".weight")):
        output_map = lightgbm.generate_context_files(
            EXAMPLE_CONFIG, EXMAPLE_CONFIG_FILE_NAME, 1)
    entrypoint_file_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh')
    entrypoint_file = None
    for k, v in output_map.items():
        if v == entrypoint_file_in_docker:
            entrypoint_file = k
    actual = open(entrypoint_file, "r").read()
    expected = """#!/bin/sh
set -e
gsutil cp -r gs://lightgbm-test/regression.train {0}/regression.train
gsutil cp -r gs://lightgbm-test/regression.test {0}/regression.test
echo 'All files are copied!'
lightgbm config={0}/config.conf
gsutil cp -r {0}/model.txt gs://lightgbm-test/model.txt
""".format(posixpath.realpath(constants.DEFAULT_DEST_PREFIX))
    print(actual)
    assert expected == actual


def test_entrypoint_content_dist_data_parallel():
    config = EXAMPLE_CONFIG.copy()
    config["tree_learner"] = "data"
    config["train_data"] = ",".join(["gs://lightgbm-test/regression.train1",
                                     "gs://lightgbm-test/regression.train2"])
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists'):
        output_map = lightgbm.generate_context_files(
            config, EXMAPLE_CONFIG_FILE_NAME, 2)
    entrypoint_file_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh')
    entrypoint_file = None
    for k, v in output_map.items():
        if v == entrypoint_file_in_docker:
            entrypoint_file = k
    actual = open(entrypoint_file, "r").read()
    expected = """#!/bin/sh
set -e
RANK=`python lightgbm_dist_training_init.py config.conf mlist.txt`
case $RANK in
	0)
		gsutil cp -r gs://lightgbm-test/regression.train1 /app/train_data
		gsutil cp -r gs://lightgbm-test/regression.train1.weight /app/train_data.weight
		;;
	1)
		gsutil cp -r gs://lightgbm-test/regression.train2 /app/train_data
		gsutil cp -r gs://lightgbm-test/regression.train2.weight /app/train_data.weight
		;;
esac
gsutil cp -r gs://lightgbm-test/regression.test {0}/regression.test
echo 'All files are copied!'
lightgbm config={0}/config.conf
gsutil cp -r {0}/model.txt gs://lightgbm-test/model.txt
""".format(posixpath.realpath(constants.DEFAULT_DEST_PREFIX))
    print(actual)
    assert expected == actual


def test_entrypoint_content_dist_data_parallel_no_weight_files():
    config = EXAMPLE_CONFIG.copy()
    config["tree_learner"] = "data"
    config["train_data"] = ",".join(["gs://lightgbm-test/regression.train1",
                                     "gs://lightgbm-test/regression.train2"])
    with patch('kubeflow.fairing.cloud.storage.GCSStorage.exists',
               new=lambda bucket, path: not path.endswith(".weight")):
        output_map = lightgbm.generate_context_files(
            config, EXMAPLE_CONFIG_FILE_NAME, 2)
    entrypoint_file_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, 'entrypoint.sh')
    entrypoint_file = None
    for k, v in output_map.items():
        if v == entrypoint_file_in_docker:
            entrypoint_file = k
    actual = open(entrypoint_file, "r").read()
    expected = """#!/bin/sh
set -e
RANK=`python lightgbm_dist_training_init.py config.conf mlist.txt`
case $RANK in
	0)
		gsutil cp -r gs://lightgbm-test/regression.train1 /app/train_data
		;;
	1)
		gsutil cp -r gs://lightgbm-test/regression.train2 /app/train_data
		;;
esac
gsutil cp -r gs://lightgbm-test/regression.test {0}/regression.test
echo 'All files are copied!'
lightgbm config={0}/config.conf
gsutil cp -r {0}/model.txt gs://lightgbm-test/model.txt
""".format(posixpath.realpath(constants.DEFAULT_DEST_PREFIX))
    print(actual)
    assert expected == actual


def test_dist_training_misconfigured_input_files():
    config = EXAMPLE_CONFIG.copy()
    config["tree_learner"] = "feature"
    config["train_data"] = ",".join(["gs://lightgbm-test/regression.train1",
                                     "gs://lightgbm-test/regression.train2"])
    with pytest.raises(RuntimeError) as excinfo:
        lightgbm.generate_context_files(config, EXMAPLE_CONFIG_FILE_NAME, 2)
    assert "train_data has more than one file specified" in str(excinfo.value)


def test_dist_training_misconfigured_num_machines():
    config = EXAMPLE_CONFIG.copy()
    config["tree_learner"] = "data"
    config["train_data"] = ",".join(["gs://lightgbm-test/regression.train1",
                                     "gs://lightgbm-test/regression.train2"])
    with pytest.raises(RuntimeError) as excinfo:
        lightgbm.generate_context_files(config, EXMAPLE_CONFIG_FILE_NAME, 3)
    assert "field in the config should be equal to the num_machines=3 config value." in str(
        excinfo.value)
