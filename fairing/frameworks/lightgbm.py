import fairing
from fairing.preprocessors.base import BasePreProcessor
from fairing.builders.append.append import AppendBuilder
from fairing.deployers.job.job import Job
from fairing.constants import constants
import tempfile
import os
import configparser
import posixpath
import stat

TRAIN_DATA_FIELDS = ["data", "train", "train_data",
                     "train_data_file", "data_filename"]
TEST_DATA_FIELDS = ["valid", "test", "valid_data", "valid_data_file", "test_data",
                    "test_data_file", "valid_filenames"]
OUTPUT_MODEL = ["output_model", "model_output", "model_out"]
ENTRYPOINT = posixpath.join(constants.DEFAULT_DEST_PREFIX, "entrypoint.sh")
LIGHTGBM_EXECUTABLE = "lightgbm"

def _load_config_file(config_file):
    config_parser = configparser.ConfigParser(allow_no_value=True)
    with open(config_file, 'r') as f:
        #Hack to get config parser work with properties files
        buf = "[default]\n" + f.read()
        config_parser.read_string(buf)
        config = dict(config_parser.items(section="default"))
    return config


def _get_config_value(config, field_names):
    buf = {}
    for field in field_names:
        if field in config:
            buf[field] = config.get(field)
    if len(buf.items()) > 1:
        raise RuntimeError(
            "More than one field alias is specified: {}".format(buf))
    if len(buf.items()) > 0:
        return list(buf.items())[0]
    else:
        return None, None


def _save_to_config_file(config, file_name=None):
    if not file_name:
        _, file_name = tempfile.mkstemp()
    
    with open(file_name, 'w') as fh:
        content = []
        for k,v in config.items():
            if isinstance(v, bool):
                v = str(v).lower()
            content.append("{}={}".format(k, v))
        fh.write("\n".join(content))
        fh.write("\n")
    return file_name


def _modify_paths_in_config(config, field_names, dst_base_dir):
    field_name, field_value = _get_config_value(config, field_names)
    if field_value is None:
        return None, None
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


def _generate_entrypoint(copy_files_before, copy_files_after, config_file):
    buf = ["#!/bin/sh", "set -e"]
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


def generate_context_files(config, config_file_name):
    output_map = {}
    copy_files_before = {}
    copy_files_after = {}

    #config will be modified inplace so taking a copy
    config = config.copy() # shallow copy is good enough
    for field_names in [TRAIN_DATA_FIELDS, TEST_DATA_FIELDS]:
        src_paths, dst_paths = _modify_paths_in_config(
            config, field_names, constants.DEFAULT_DEST_PREFIX)
        _update_maps(output_map, copy_files_before, src_paths, dst_paths)

    src_paths, dst_paths = _modify_paths_in_config(
        config, OUTPUT_MODEL, constants.DEFAULT_DEST_PREFIX)
    _update_maps(output_map, copy_files_after, src_paths, dst_paths)

    if len(output_map) + len(copy_files_before) == 0:
        raise RuntimeError("Both train and test data is missing in the config")
    modified_config_file_name = _save_to_config_file(config)
    config_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, "config.conf")
    output_map[modified_config_file_name] = config_in_docker
    output_map[config_file_name] = config_in_docker + ".original"
    entrypoint_file_name = _generate_entrypoint(
        copy_files_before, copy_files_after, config_in_docker)
    output_map[entrypoint_file_name] = ENTRYPOINT

    return output_map


def execute(config, docker_registry, base_image, namespace=None):
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
    if namespace is None:
        namespace = "kubeflow"

    config_file_name = None
    if isinstance(config, str):
        config_file_name = config
        config = _load_config_file(config)
    elif isinstance(config, dict):
        config_file_name = _save_to_config_file(config)
    else:
        raise RuntimeError("config should be of type dict or string(filepath) "
                           "but got {}".format(type(dict)))

    output_map = generate_context_files(config, config_file_name)

    preprocessor = BasePreProcessor(
        command=[ENTRYPOINT], output_map=output_map)
    builder = AppendBuilder(registry=docker_registry,
                            base_image=base_image, preprocessor=preprocessor)
    builder.build()
    pod_spec = builder.generate_pod_spec()
    deployer = Job(namespace=namespace, pod_spec_mutators=[
                   fairing.cloud.gcp.add_gcp_credentials_if_exists])
    deployer.deploy(pod_spec)
