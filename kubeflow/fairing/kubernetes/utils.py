from kubernetes import client
from kubernetes.client.models.v1_resource_requirements import V1ResourceRequirements
from kubeflow.fairing.constants import constants


def get_resource_mutator(cpu=None, memory=None):
    """The mutator for getting the resource setting for pod spec.

    The useful example:
    https://github.com/kubeflow/fairing/blob/master/examples/train_job_api/main.ipynb

    :param cpu: Limits and requests for CPU resources (Default value = None)
    :param memory: Limits and requests for memory (Default value = None)
    :returns: object: The mutator function for setting cpu and memory in pod spec.

    """
    def _resource_mutator(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        if cpu is None and memory is None:
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
            if pod_spec.containers[0].resources:
                if pod_spec.containers[0].resources.limits:
                    pod_spec.containers[0].resources.limits = {}
                for k, v in limits.items():
                    pod_spec.containers[0].resources.limits[k] = v
            else:
                pod_spec.containers[0].resources = V1ResourceRequirements(limits=limits)
    return _resource_mutator


def mounting_pvc(pvc_name, pvc_mount_path=constants.PVC_DEFAULT_MOUNT_PATH):
    """The function for pod_spec_mutators to mount persistent volume claim.

    :param pvc_name: The name of persistent volume claim
    :param pvc_mount_path: Path for the persistent volume claim mounts to.
    :returns: object: function for mount the pvc to pods.

    """
    mounting_name = str(constants.PVC_DEFAULT_VOLUME_NAME) + pvc_name
    def _mounting_pvc(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        volume_mount = client.V1VolumeMount(
            name=mounting_name, mount_path=pvc_mount_path)
        if pod_spec.containers[0].volume_mounts:
            pod_spec.containers[0].volume_mounts.append(volume_mount)
        else:
            pod_spec.containers[0].volume_mounts = [volume_mount]

        volume = client.V1Volume(
            name=mounting_name,
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name))
        if pod_spec.volumes:
            pod_spec.volumes.append(volume)
        else:
            pod_spec.volumes = [volume]
    return _mounting_pvc
