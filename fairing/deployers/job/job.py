import logging
import json
import uuid

from kubernetes import client as k8s_client

from fairing import utils
from fairing.kubernetes.manager import KubeManager
from fairing.deployers.deployer import DeployerInterface


logger = logging.getLogger(__name__)
DEFAULT_JOB_NAME = 'fairing-job-'
DEPLOPYER_TYPE = 'job'


class Job(DeployerInterface):
    """Handle all the k8s' template building for a training 
    Attributes:
        namespace: k8s namespace where the training's components 
            will be deployed.
        runs: Number of training(s) to be deployed. Hyperparameter search
            will generate multiple jobs.
    """

    def __init__(self, namespace=None, runs=1, output=None,
                 cleanup=True, labels=None, job_name=DEFAULT_JOB_NAME,
                 stream_log=True, deployer_type=DEPLOPYER_TYPE,
                 mount_credentials=False):
        if namespace is None:
            self.namespace = utils.get_default_target_namespace()
        else:
            self.namespace = namespace

        # Used as pod and job name
        self.job_name = job_name
        self.deployment_spec = None
        self.runs = runs
        self.output = output
        self.backend = KubeManager()
        self.cleanup = cleanup
        self.stream_log = stream_log
        self.set_labels(labels, deployer_type)
        self.mount_credentials = mount_credentials

    def set_labels(self, labels, deployer_type):
        self.labels = {'fairing-deployer': deployer_type}
        if labels:
            self.labels.update(labels)

    def add_credentials_to_pod_spec(self, pod_spec):
        # TODO: Extract config options into a global config set, in order to
        # enable platform-specific options.

        if not self.backend.secret_exists('user-gcp-sa', self.namespace):
            raise ValueError('Unable to mount credentials: '
            + 'Secret user-gcp-sa not found in namespace {}'.format(self.namespace))

        # Set appropriate secrets and volumes to enable kubeflow-user service
        # account.
        env_var = k8s_client.V1EnvVar(
            name='GOOGLE_APPLICATION_CREDENTIALS',
            value='/etc/secrets/user-gcp-sa.json')
        if pod_spec.containers[0].env:
            pod_spec.containers[0].env.append(env_var)
        else:
            pod_spec.containers[0].env = [env_var]

        volume_mount = k8s_client.V1VolumeMount(
            name='user-gcp-sa', mount_path='/etc/secrets', read_only=True)
        if pod_spec.containers[0].volume_mounts:
            pod_spec.containers[0].volume_mounts.append(volume_mount)
        else:
            pod_spec.containers[0].volume_mounts = [volume_mount]

        volume = k8s_client.V1Volume(
            name='user-gcp-sa',
            secret=k8s_client.V1SecretVolumeSource(secret_name='user-gcp-sa'))
        if pod_spec.volumes:
            pod_spec.volumes.append(volume)
        else:
            pod_spec.volumes = [volume]

    def deploy(self, pod_spec):
        self.job_id = str(uuid.uuid1())
        self.labels['fairing-id'] = self.job_id
        if self.mount_credentials:
            self.add_credentials_to_pod_spec(pod_spec)
        pod_template_spec = self.generate_pod_template_spec(pod_spec)
        pod_template_spec.spec.restart_policy = 'Never'
        self.deployment_spec = self.generate_deployment_spec(pod_template_spec)
        if self.output:
            api = k8s_client.ApiClient()
            job_output = api.sanitize_for_serialization(self.deployment_spec)
            print(json.dumps(job_output))

        name = self.create_resource()
        logger.warn("Training job {} launched.".format(name))

        if self.stream_log:
            self.get_logs()

    def create_resource(self):
        self._created_job = self.backend.create_job(self.namespace, self.deployment_spec)
        return self._created_job.metadata.name

    def generate_pod_template_spec(self, pod_spec):
        """Generate a V1PodTemplateSpec initiazlied with correct metadata
            and with the provided pod_spec"""
        if not isinstance(pod_spec, k8s_client.V1PodSpec):
            raise TypeError('pod_spec must be a V1PodSpec, but got %s'
                            % type(pod_spec))
        return k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(name="fairing-deployer", labels=self.labels),
            spec=pod_spec)
        
    def generate_deployment_spec(self, pod_template_spec):
        """Generate a V1Job initialized with correct completion and
         parallelism (for HP search) and with the provided V1PodTemplateSpec"""
        if not isinstance(pod_template_spec, k8s_client.V1PodTemplateSpec):
            raise TypeError( """pod_template_spec must be a V1PodTemplateSpec,
                but got %s""" % type(pod_template_spec))

        job_spec = k8s_client.V1JobSpec(
            template=pod_template_spec,
            parallelism=self.runs,
            completions=self.runs)
        
        return k8s_client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=k8s_client.V1ObjectMeta(
                generate_name=self.job_name
            ),
            spec=job_spec
        )

    def get_logs(self):
        self.backend.log(self._created_job.metadata.name, self._created_job.metadata.namespace, self.labels)

        if self.cleanup:
            self.do_cleanup()

    def do_cleanup(self):
        logger.warn("Cleaning up job {}...".format(self._created_job.metadata.name))
        k8s_client.BatchV1Api().delete_namespaced_job(
            self._created_job.metadata.name,
            self._created_job.metadata.namespace,
            body=k8s_client.V1DeleteOptions(propagation_policy='Foreground'))
