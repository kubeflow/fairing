import fairing
from fairing.preprocessors.base import BasePreProcessor
from fairing.builders.append.append import AppendBuilder
from fairing.deployers.job.job import Job
from fairing.deployers.tfjob.tfjob import TfJob
from fairing.constants import constants
from configparser import ConfigParser
from . import lightgbm_dist_training_init
from . import utils
import tempfile
import os
import posixpath
import stat
import logging

logger = logging.getLogger(__name__)

TRAIN_DATA_FIELDS = ["data", "train", "train_data",
                     "train_data_file", "data_filename"]
TEST_DATA_FIELDS = ["valid", "test", "valid_data", "valid_data_file", "test_data",
                    "test_data_file", "valid_filenames"]
NUM_MACHINES_FILEDS = ["num_machines", "num_machine"]
PORT_FIELDS = ["local_listen_port", "local_port"]
MLIST_FIELDS = ["machine_list_filename",
                "machine_list_file", "machine_list", "mlist"]
OUTPUT_MODEL_FIELDS = ["output_model", "model_output", "model_out"]
INPUT_MODEL_FIELDS = ["input_model", "model_input", "model_in"]
OUTPUT_RESULT_FIELDS = ["output_result", "predict_result", "prediction_result", 
                        "predict_name", "prediction_name", "pred_name", "name_pred"]
MACHINE_FIELDS = ["machines", "workers", "nodes"]
ENTRYPOINT = posixpath.join(constants.DEFAULT_DEST_PREFIX, "entrypoint.sh")
LIGHTGBM_EXECUTABLE = "lightgbm"
CONFIG_FILE_NAME = "config.conf"
MLIST_FILE_NAME = "mlist.txt"
BLACKLISTED_FIELDS = PORT_FIELDS + MLIST_FIELDS + MACHINE_FIELDS


def _modify_paths_in_config(config, field_names, dst_base_dir):
    field_name, field_value = utils.get_config_value(config, field_names)
    if field_value is None:
        return [], []
    src_paths = field_value.split(",")
    dst_paths = []
    for src_path in src_paths:
        file_name = os.path.split(src_path)[-1]
        dst_paths.append(posixpath.join(dst_base_dir, file_name))
    config[field_name] = ",".join(dst_paths)
    return src_paths, dst_paths


def _update_maps(output_map, copy_files, src_paths, dst_paths):
    for src_path, dst_path in zip(src_paths, dst_paths):
        if os.path.exists(src_path):
            output_map[src_path] = dst_path
        else:
            copy_files[src_path] = dst_path


def _generate_entrypoint(copy_files_before, copy_files_after, config_file, init_cmds=None):
    buf = ["#!/bin/sh",
           "set -e"]
    if init_cmds:
        buf.extend(init_cmds)

    for k, v in copy_files_before.items():
        copy_cmd = _get_cmd_for_file_transfer(k)
        buf.append("{} cp {} {}".format(copy_cmd, k, v))
    buf.append("echo 'All files are copied!'")
    buf.append("{} config={}".format(LIGHTGBM_EXECUTABLE, config_file))
    for k, v in copy_files_after.items():
        copy_cmd = _get_cmd_for_file_transfer(k)
        buf.append("{} cp {} {}".format(copy_cmd, v, k))
    _, file_name = tempfile.mkstemp()
    with open(file_name, 'w') as fh:
        content = "\n".join(buf)
        fh.write(content)
        fh.write("\n")
    st = os.stat(file_name)
    os.chmod(file_name, st.st_mode | stat.S_IEXEC)
    return file_name

# Using shell commands to do the file copy instead of using python libs
# CLIs like gsutil, s3cmd are optimized and can be easily configured by
# the user using boto.cfg in the base docker image.


def _get_cmd_for_file_transfer(src_path):
    if src_path.startswith("gcs://") or src_path.startswith("gs://"):
        return "gsutil"
    else:
        raise RuntimeError("can't find a copy command for {}".format(src_path))


def generate_context_files(config, config_file_name, distributed):
    output_map = {}
    copy_files_before = {}
    copy_files_after = {}

    # config will be modified inplace so taking a copy
    config = config.copy()  # shallow copy is good enough
    remote_files = [(copy_files_before,
                        [TRAIN_DATA_FIELDS, TEST_DATA_FIELDS, INPUT_MODEL_FIELDS]),
                    (copy_files_after,
                        [OUTPUT_MODEL_FIELDS, OUTPUT_RESULT_FIELDS])]
    for copy_files, field_names_list in remote_files:
        for field_names in field_names_list:
            src_paths, dst_paths = _modify_paths_in_config(
                config, field_names, constants.DEFAULT_DEST_PREFIX)
            _update_maps(output_map, copy_files, src_paths, dst_paths)

    if len(output_map) + len(copy_files_before) == 0:
        raise RuntimeError("Both train and test data is missing in the config")
    modified_config_file_name = utils.save_properties_config_file(config)
    config_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, CONFIG_FILE_NAME)
    output_map[modified_config_file_name] = config_in_docker
    output_map[config_file_name] = config_in_docker + ".original"

    init_cmds = None
    if distributed:
        init_file = lightgbm_dist_training_init.__file__
        init_file_name = os.path.split(init_file)[1]
        output_map[init_file] = os.path.join(
            constants.DEFAULT_DEST_PREFIX, init_file_name)
        init_cmds = ["python {} {} {}".format(init_file_name,
                                              CONFIG_FILE_NAME,
                                              MLIST_FILE_NAME)]
    entrypoint_file_name = _generate_entrypoint(
        copy_files_before, copy_files_after, config_in_docker, init_cmds)
    output_map[entrypoint_file_name] = ENTRYPOINT
    output_map[utils.__file__] = os.path.join(
        constants.DEFAULT_DEST_PREFIX, "utils.py")

    return output_map


def execute(config,
            docker_registry,
            base_image="gcr.io/kubeflow-fairing/lightgbm:latest",
            namespace="kubeflow"):
    """
    Runs the LightGBM CLI in a single pod in user's Kubeflow cluster.
    Users can configure it to be a train, predict, and other supported tasks
    by using the right config.
    Please refere https://github.com/microsoft/LightGBM/blob/master/docs/Parameters.rst
    for more information on config options.
    Attributes:
        config: LightGBM config - Ref https://github.com/microsoft/LightGBM/blob/master/docs/Parameters.rst
        docker_registry: registry to push the built docker image
        base_image: base image to use for this job. It should have lightgbm installed and should be in PATH variable.
        namespace: Kubernetes namespace to use
    """

    config_file_name = None
    if isinstance(config, str):
        config_file_name = config
        config = utils.load_properties_config_file(config)
    elif isinstance(config, dict):
        config_file_name = utils.save_properties_config_file(config)
    else:
        raise RuntimeError("config should be of type dict or string(filepath) "
                           "but got {}".format(type(dict)))

    utils.scrub_fields(config, BLACKLISTED_FIELDS)

    _, num_machines = utils.get_config_value(config, NUM_MACHINES_FILEDS)
    num_machines = num_machines or 1
    if num_machines:
        try:
            num_machines = int(num_machines)
        except ValueError:
            raise ValueError("num_machines value in config should be an int >= 1 "
                             "but got {}".format(config.get('num_machines')))
        if num_machines < 1:
            raise ValueError(
                "num_machines value in config should >= 1 but got {}".format(num_machines))

    if num_machines > 1:
        config['machine_list_file'] = "mlist.txt"
    output_map = generate_context_files(
        config, config_file_name, num_machines > 1)

    preprocessor = BasePreProcessor(
        command=[ENTRYPOINT], output_map=output_map)
    builder = AppendBuilder(registry=docker_registry,
                            base_image=base_image, preprocessor=preprocessor)
    builder.build()
    pod_spec = builder.generate_pod_spec()

    if num_machines == 1:
        # non-distributed mode
        deployer = Job(namespace=namespace, pod_spec_mutators=[
            fairing.cloud.gcp.add_gcp_credentials_if_exists])
    else:
        # distributed mode
        deployer = TfJob(namespace=namespace, pod_spec_mutators=[
            fairing.cloud.gcp.add_gcp_credentials_if_exists],
            chief_count=1,
            worker_count=num_machines-1)
    deployer.deploy(pod_spec)
