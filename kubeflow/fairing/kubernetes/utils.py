import logging
from kubernetes import client
from kubernetes.client.models.v1_resource_requirements import V1ResourceRequirements
from kubeflow.fairing.constants import constants

logger = logging.getLogger(__name__)

def get_resource_mutator(cpu=None, memory=None, gpu=None, gpu_vendor='nvidia'):
    """The mutator for getting the resource setting for pod spec.

    The useful example:
    https://github.com/kubeflow/fairing/blob/master/examples/train_job_api/main.ipynb

    :param cpu: Limits and requests for CPU resources (Default value = None)
    :param memory: Limits and requests for memory (Default value = None)
    :param gpu: Limits for GPU (Default value = None)
    :param gpu_vendor: Default value is 'nvidia', also can be set to 'amd'.
    :returns: object: The mutator function for setting cpu and memory in pod spec.

    """
    def _resource_mutator(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        if cpu is None and memory is None and gpu is None:
            return
        if pod_spec.containers and len(pod_spec.containers) >= 1:
            # All cloud providers specify their instace memory in GB
            # so it is peferable for user to specify memory in GB
            # and we convert it to Gi that K8s needs
            limits = {}
            if cpu:
                limits['cpu'] = cpu
            if memory:
                memory_gib = "{}Gi".format(round(memory/1.073741824, 2))
                limits['memory'] = memory_gib
            if gpu:
                limits[gpu_vendor + '.com/gpu'] = gpu
            if pod_spec.containers[0].resources:
                if pod_spec.containers[0].resources.limits:
                    pod_spec.containers[0].resources.limits = {}
                for k, v in limits.items():
                    pod_spec.containers[0].resources.limits[k] = v
            else:
                pod_spec.containers[0].resources = V1ResourceRequirements(limits=limits)
    return _resource_mutator


def mounting_pvc(pvc_name, pvc_mount_path=constants.PVC_DEFAULT_MOUNT_PATH):
    """The function has been deprecated, please use `volume_mounts`.

    """
    logger.warning("The function mounting_pvc has been deprecated, \
                    please use `volume_mounts`")

    return volume_mounts('pvc', pvc_name, mount_path=pvc_mount_path)


def volume_mounts(volume_type, volume_name, mount_path, sub_path=None):
    """The function for pod_spec_mutators to mount volumes.

    :param volume_type: support type: secret, config_map and pvc
    :param name: The name of volume
    :param mount_path: Path for the volume mounts to.
    :param sub_path: SubPath for the volume mounts to (Default value = None).
    :returns: object: function for mount the pvc to pods.

    """
    mount_name = str(constants.DEFAULT_VOLUME_NAME) + volume_name

    def _volume_mounts(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        volume_mount = client.V1VolumeMount(
            name=mount_name, mount_path=mount_path, sub_path=sub_path)
        if pod_spec.containers[0].volume_mounts:
            pod_spec.containers[0].volume_mounts.append(volume_mount)
        else:
            pod_spec.containers[0].volume_mounts = [volume_mount]

        if volume_type == 'pvc':
            volume = client.V1Volume(
                name=mount_name,
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=volume_name))
        elif volume_type == 'secret':
            volume = client.V1Volume(
                name=mount_name,
                secret=client.V1SecretVolumeSource(secret_name=volume_name))
        elif volume_type == 'config_map':
            volume = client.V1Volume(
                name=mount_name,
                config_map=client.V1ConfigMapVolumeSource(name=volume_name))
        else:
            raise RuntimeError("Unsupport type %s" % volume_type)

        if pod_spec.volumes:
            pod_spec.volumes.append(volume)
        else:
            pod_spec.volumes = [volume]
    return _volume_mounts

def add_env(env_vars):
    """The function for pod_spec_mutators to add custom environment vars.

    :param vars: dict of custom environment vars.
    :returns: object: function for add environment vars to pods.

    """
    def _add_env(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        env_list = []
        for env_name, env_value in env_vars.items():
            env_list.append(client.V1EnvVar(name=env_name, value=env_value))

        if pod_spec.containers and len(pod_spec.containers) >= 1:
            if pod_spec.containers[0].env:
                pod_spec.containers[0].env.extend(env_list)
            else:
                pod_spec.containers[0].env = env_list
    return _add_env
