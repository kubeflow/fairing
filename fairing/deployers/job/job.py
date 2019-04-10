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
                 pod_spec_mutators=None):
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
        self.pod_spec_mutators = pod_spec_mutators or []

    def set_labels(self, labels, deployer_type):
        self.labels = {'fairing-deployer': deployer_type}
        if labels:
            self.labels.update(labels)

    def deploy(self, pod_spec):
        self.job_id = str(uuid.uuid1())
        self.labels['fairing-id'] = self.job_id
        for fn in self.pod_spec_mutators:
            fn(self.backend, pod_spec, self.namespace)
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
                generate_name=self.job_name,
                labels=self.labels,
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
