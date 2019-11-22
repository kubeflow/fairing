import tempfile
import os
import posixpath
import stat
import logging
import collections

from kubeflow.fairing import utils as fairing_utils
from kubeflow.fairing.preprocessors.base import BasePreProcessor
from kubeflow.fairing.builders.append.append import AppendBuilder
from kubeflow.fairing.deployers.job.job import Job
from kubeflow.fairing.deployers.tfjob.tfjob import TfJob
from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes import utils as k8s_utils
from kubeflow.fairing.cloud import storage
from kubeflow.fairing.cloud import gcp
from kubeflow.fairing.frameworks import lightgbm_dist_training_init
from kubeflow.fairing.frameworks import utils

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
TREE_LEARNER_FIELDS = ["tree_learner",
                       "tree", "tree_type", "tree_learner_type"]
ENTRYPOINT = posixpath.join(constants.DEFAULT_DEST_PREFIX, "entrypoint.sh")
LIGHTGBM_EXECUTABLE = "lightgbm"
CONFIG_FILE_NAME = "config.conf"
MLIST_FILE_NAME = "mlist.txt"
BLACKLISTED_FIELDS = PORT_FIELDS + MLIST_FIELDS + MACHINE_FIELDS
WEIGHT_FILE_EXT = ".weight"
DATA_PARALLEL_MODES = ["data", "voting"]


def _modify_paths_in_config(config, field_names, dst_base_dir):
    """modify lightgbm config fields

    :param config: config entries
    :param field_names: list of fields
    :param dst_base_dir: path to destination directory

    """
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
    """update maps

    :param output_map: output map entries
    :param copy_files: files to be copied
    :param src_paths: source paths
    :param dst_paths: destination paths

    """
    for src_path, dst_path in zip(src_paths, dst_paths):
        if os.path.exists(src_path):
            output_map[src_path] = dst_path
        else:
            copy_files[src_path] = dst_path


def _get_commands_for_file_ransfer(files_map):
    """get commands for file transfer

    :param files_map: files to be mapped

    """
    cmds = []
    for k, v in files_map.items():
        storage_obj = storage.get_storage_class(k)()
        if storage_obj.exists(k):
            cmds.append(storage_obj.copy_cmd(k, v))
        else:
            raise RuntimeError("Remote file {} does't exist".format(k))
    return cmds


def _generate_entrypoint(copy_files_before, copy_files_after, config_file,
                         init_cmds=None, copy_patitioned_files=None):
    """ generate entry point

    :param copy_files_before: previous copied files
    :param copy_files_after: files to be copied
    :param config_file: path to config file
    :param init_cmds:  commands(Default value = None)
    :param copy_patitioned_files:  (Default value = None)

    """
    buf = ["#!/bin/sh",
           "set -e"]
    if init_cmds:
        buf.extend(init_cmds)
    # In data prallel mode, copying files based on RANK of the worker in the cluster.
    # The data is partitioned (#partitions=#workers) and each worker gets one partition of the data.
    if copy_patitioned_files and len(copy_patitioned_files) > 0: #pylint:disable=len-as-condition
        buf.append("case $RANK in")
        for rank, files in copy_patitioned_files.items():
            buf.append("\t{})".format(rank))
            buf.extend(
                ["\t\t" + cmd for cmd in _get_commands_for_file_ransfer(files)])
            buf.append("\t\t;;")
        buf.append("esac")

    # copying files that are common to all workers
    buf.extend(_get_commands_for_file_ransfer(copy_files_before))

    buf.append("echo 'All files are copied!'")
    buf.append("{} config={}".format(LIGHTGBM_EXECUTABLE, config_file))
    for k, v in copy_files_after.items():
        storage_obj = storage.get_storage_class(k)()
        buf.append(storage_obj.copy_cmd(v, k))
    _, file_name = tempfile.mkstemp()
    with open(file_name, 'w') as fh:
        content = "\n".join(buf)
        fh.write(content)
        fh.write("\n")
    st = os.stat(file_name)
    os.chmod(file_name, st.st_mode | stat.S_IEXEC)
    return file_name


def _add_train_weight_file(config, dst_base_dir):
    """add train weight file

    :param config: config entries
    :param dst_base_dir: destination directory

    """
    _, field_value = utils.get_config_value(config, TRAIN_DATA_FIELDS)
    if field_value is None:
        return [], []
    else:
        src_paths = field_value.split(",")
        weight_paths = [x+WEIGHT_FILE_EXT for x in src_paths]
        weight_paths_found = []
        weight_paths_dst = []
        for path in weight_paths:
            found = os.path.exists(path)
            if not found:
                # in case the path is local and doesn't exist
                storage_class = storage.lookup_storage_class(path)
                if storage_class:
                    found = storage_class().exists(path)
            if found:
                weight_paths_found.append(path)
                file_name = os.path.split(path)[-1]
                weight_paths_dst.append(
                    posixpath.join(dst_base_dir, file_name))
        return weight_paths_found, weight_paths_dst


def generate_context_files(config, config_file_name, num_machines):
    """generate context files

    :param config: config entries
    :param config_file_name: config file name
    :param num_machines: number of machines

    """
    # Using ordered dict to have consistent behaviour around order in which
    # files are copied in the worker nodes.
    output_map = collections.OrderedDict()
    copy_files_before = collections.OrderedDict()
    copy_files_after = collections.OrderedDict()
    copy_patitioned_files = collections.OrderedDict()

    # config will be modified inplace in this function so taking a copy
    config = config.copy()  # shallow copy is good enough

    _, tree_learner = utils.get_config_value(config, TREE_LEARNER_FIELDS)
    parition_data = tree_learner and tree_learner.lower() in DATA_PARALLEL_MODES
    remote_files = [(copy_files_before,
                     [TEST_DATA_FIELDS, INPUT_MODEL_FIELDS]),
                    (copy_files_after,
                     [OUTPUT_MODEL_FIELDS, OUTPUT_RESULT_FIELDS])]

    if parition_data:
        train_data_field, train_data_value = utils.get_config_value(
            config, TRAIN_DATA_FIELDS)
        train_files = train_data_value.split(",")
        if len(train_files) != num_machines:
            raise RuntimeError("#Training files listed in the {}={} field in the config should be "
                               "equal to the num_machines={} config value."\
                                .format(train_data_field, train_data_value, num_machines))
        weight_src_paths, weight_dst_paths = _add_train_weight_file(config,
                                                                    constants.DEFAULT_DEST_PREFIX)
        dst = posixpath.join(constants.DEFAULT_DEST_PREFIX, "train_data")
        config[train_data_field] = dst
        for i, f in enumerate(train_files):
            copy_patitioned_files[i] = collections.OrderedDict()
            copy_patitioned_files[i][f] = dst
            if f+WEIGHT_FILE_EXT in weight_src_paths:
                copy_patitioned_files[i][f +
                                         WEIGHT_FILE_EXT] = dst+WEIGHT_FILE_EXT
    else:
        train_data_field, train_data_value = utils.get_config_value(
            config, TRAIN_DATA_FIELDS)
        if len(train_data_value.split(",")) > 1:
            raise RuntimeError("{} has more than one file specified but tree-learner is set to {} "
                               "which can't handle multiple files. For distributing data across "
                               "multiple workers, please use one of {} as a tree-learner method. "
                               "For more information please refer the LightGBM parallel guide"
                               " https://github.com/microsoft/LightGBM/blob/master/docs/"
                               "Parallel-Learning-Guide.rst".format(
                                   train_data_field, tree_learner, DATA_PARALLEL_MODES))
        remote_files[0][1].insert(0, TRAIN_DATA_FIELDS)
        weight_src_paths, weight_dst_paths = _add_train_weight_file(config,
                                                                    constants.DEFAULT_DEST_PREFIX)
        _update_maps(output_map, copy_files_before, weight_src_paths, weight_dst_paths)

    for copy_files, field_names_list in remote_files:
        for field_names in field_names_list:
            src_paths, dst_paths = _modify_paths_in_config(
                config, field_names, constants.DEFAULT_DEST_PREFIX)
            _update_maps(output_map, copy_files, src_paths, dst_paths)

    if len(output_map) + len(copy_files_before) + len(copy_patitioned_files) == 0:
        raise RuntimeError("Both train and test data is missing in the config")
    modified_config_file_name = utils.save_properties_config_file(config)
    config_in_docker = posixpath.join(
        constants.DEFAULT_DEST_PREFIX, CONFIG_FILE_NAME)
    output_map[modified_config_file_name] = config_in_docker
    output_map[config_file_name] = config_in_docker + ".original"

    init_cmds = None
    if num_machines > 1:
        init_file = lightgbm_dist_training_init.__file__
        init_file_name = os.path.split(init_file)[1]
        output_map[init_file] = os.path.join(
            constants.DEFAULT_DEST_PREFIX, init_file_name)
        init_cmds = ["RANK=`python {} {} {}`".format(init_file_name,
                                                     CONFIG_FILE_NAME,
                                                     MLIST_FILE_NAME)]
    entrypoint_file_name = _generate_entrypoint(
        copy_files_before, copy_files_after, config_in_docker, init_cmds, copy_patitioned_files)
    output_map[entrypoint_file_name] = ENTRYPOINT
    output_map[utils.__file__] = os.path.join(
        constants.DEFAULT_DEST_PREFIX, "utils.py")

    return output_map


def execute(config,
            docker_registry,
            base_image="gcr.io/kubeflow-fairing/lightgbm:latest",
            namespace=None,
            stream_log=True,
            cores_per_worker=None,
            memory_per_worker=None,
            pod_spec_mutators=None):
    """Runs the LightGBM CLI in a single pod in user's Kubeflow cluster.
    Users can configure it to be a train, predict, and other supported tasks
    by using the right config.
    Please refere https://github.com/microsoft/LightGBM/blob/master/docs/Parameters.rst
    for more information on config options.

    :param config: config entries
    :param docker_registry: docker registry name
    :param base_image: base image (Default value = "gcr.io/kubeflow-fairing/lightgbm:latest")
    :param namespace: k8s namespace (Default value = None)
    :param stream_log: should that stream log? (Default value = True)
    :param cores_per_worker: number of cores per worker (Default value = None)
    :param memory_per_worker: memory value per worker (Default value = None)
    :param pod_spec_mutators: pod spec mutators (Default value = None)

    """
    if not namespace and not fairing_utils.is_running_in_k8s():
        namespace = "kubeflow"
    namespace = namespace or fairing_utils.get_default_target_namespace()
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
        config, config_file_name, num_machines)

    preprocessor = BasePreProcessor(
        command=[ENTRYPOINT], output_map=output_map)
    builder = AppendBuilder(registry=docker_registry,
                            base_image=base_image, preprocessor=preprocessor)
    builder.build()
    pod_spec = builder.generate_pod_spec()

    pod_spec_mutators = pod_spec_mutators or []
    pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)
    pod_spec_mutators.append(k8s_utils.get_resource_mutator(
        cores_per_worker, memory_per_worker))

    if num_machines == 1:
        # non-distributed mode
        deployer = Job(namespace=namespace,
                       pod_spec_mutators=pod_spec_mutators,
                       stream_log=stream_log)
    else:
        # distributed mode
        deployer = TfJob(namespace=namespace,
                         pod_spec_mutators=pod_spec_mutators,
                         chief_count=1,
                         worker_count=num_machines-1,
                         stream_log=stream_log)
    deployer.deploy(pod_spec)
    return deployer
