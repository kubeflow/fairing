from kubernetes import client

from fairing.constants import constants

def add_pvc_to_pod_spec(kube_manager, pod_spec, namespace, pvc_name, 
                     pvc_mount_path=None):

    if pvc_mount_path is None:
        pvc_mount_path = constants.PVC_DEFAULT_MOUNT_PATH

    volume_mount = client.V1VolumeMount(
        name=constants.PVC_DEFAULT_VOLUME_NAME, mount_path=pvc_mount_path)
    if pod_spec.containers[0].volume_mounts:
        pod_spec.containers[0].volume_mounts.append(volume_mount)
    else:
        pod_spec.containers[0].volume_mounts = [volume_mount]

    volume = client.V1Volume(
        name=constants.PVC_DEFAULT_VOLUME_NAME,
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name))
    if pod_spec.volumes:
        pod_spec.volumes.append(volume)
    else:
        pod_spec.volumes = [volume]
