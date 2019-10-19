import logging
import json
import uuid

from kubernetes import client as k8s_client

from kubeflow.fairing import utils
from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes.manager import KubeManager
from kubeflow.fairing.deployers.deployer import DeployerInterface


logger = logging.getLogger(__name__)


class Job(DeployerInterface): #pylint:disable=too-many-instance-attributes
    """Handle all the k8s' template building for a training"""

    def __init__(self, namespace=None, runs=1, output=None,
                 cleanup=True, labels=None, job_name=constants.JOB_DEFAULT_NAME,
                 stream_log=True, deployer_type=constants.JOB_DEPLOPYER_TYPE,
                 pod_spec_mutators=None, annotations=None):
        """

        :param namespace: k8s namespace where the training's components will be deployed.
        :param runs: Number of training(s) to be deployed. Hyperparameter search
                will generate multiple jobs.
        :param output: output
        :param cleanup: clean up deletes components after job finished
        :param labels: labels to be assigned to the training job
        :param job_name: name of the job
        :param stream_log: stream the log?
        :param deployer_type: type of deployer
        :param pod_spec_mutators: pod spec mutators (Default value = None)
        """
        if namespace is None:
            self.namespace = utils.get_default_target_namespace()
        else:
            self.namespace = namespace

        # Used as pod and job name
        self.job_name = job_name
        self.deployer_type = deployer_type
        self.deployment_spec = None
        self.runs = runs
        self.output = output
        self.backend = KubeManager()
        self.cleanup = cleanup
        self.stream_log = stream_log
        self.set_labels(labels, deployer_type)
        self.set_anotations(annotations)
        self.pod_spec_mutators = pod_spec_mutators or []

    def set_anotations(self, annotations):
        self.annotations = {}
        if annotations:
            self.annotations.update(annotations)

    def set_labels(self, labels, deployer_type):
        """set labels for the pods of a deployed job

        :param labels: dictionary of labels {label_name:label_value}
        :param deployer_type: deployer type name

        """
        self.labels = {'fairing-deployer': deployer_type}
        if labels:
            self.labels.update(labels)

    def deploy(self, pod_spec): #pylint:disable=arguments-differ
        """deploy the training job using k8s client lib

        :param pod_spec: pod spec of deployed training job

        """
        self.job_id = str(uuid.uuid1())
        self.labels['fairing-id'] = self.job_id
        for fn in self.pod_spec_mutators:
            fn(self.backend, pod_spec, self.namespace)
        pod_template_spec = self.generate_pod_template_spec(pod_spec)
        pod_template_spec.spec.restart_policy = 'Never'
        pod_template_spec.spec.containers[0].name = 'fairing-job'
        self.deployment_spec = self.generate_deployment_spec(pod_template_spec)
        if self.output:
            api = k8s_client.ApiClient()
            job_output = api.sanitize_for_serialization(self.deployment_spec)
            print(json.dumps(job_output))

        name = self.create_resource()
        logger.warning("The {} {} launched.".format(self.deployer_type, name))

        if self.stream_log:
            self.get_logs()

        return name

    def create_resource(self):
        """ create job"""
        self._created_job = self.backend.create_job(self.namespace, self.deployment_spec)
        return self._created_job.metadata.name

    def generate_pod_template_spec(self, pod_spec):
        """Generate a V1PodTemplateSpec initiazlied with correct metadata
            and with the provided pod_spec

        :param pod_spec: pod spec

        """
        if not isinstance(pod_spec, k8s_client.V1PodSpec):
            raise TypeError('pod_spec must be a V1PodSpec, but got %s'
                            % type(pod_spec))
        if not self.annotations:
            self.annotations = {'sidecar.istio.io/inject': 'false'}
        else:
            self.annotations['sidecar.istio.io/inject'] = 'false'
        return k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(name="fairing-deployer",
                                             annotations=self.annotations,
                                             labels=self.labels),
            spec=pod_spec)

    def generate_deployment_spec(self, pod_template_spec):
        """Generate a V1Job initialized with correct completion and
         parallelism (for HP search) and with the provided V1PodTemplateSpec

        :param pod_template_spec: V1PodTemplateSpec

        """
        if not isinstance(pod_template_spec, k8s_client.V1PodTemplateSpec):
            raise TypeError("""pod_template_spec must be a V1PodTemplateSpec,
                but got %s""" % type(pod_template_spec))

        job_spec = k8s_client.V1JobSpec(
            template=pod_template_spec,
            parallelism=self.runs,
            completions=self.runs,
            backoff_limit=0,
        )

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
        """ get logs from the deployed job"""
        self.backend.log(self._created_job.metadata.name,
                         self._created_job.metadata.namespace,
                         self.labels,
                         container="fairing-job")

        if self.cleanup:
            self.do_cleanup()

    def do_cleanup(self):
        """ clean up the pods after job finished"""
        logger.warning("Cleaning up job {}...".format(self._created_job.metadata.name))
        k8s_client.BatchV1Api().delete_namespaced_job(
            self._created_job.metadata.name,
            self._created_job.metadata.namespace,
            body=k8s_client.V1DeleteOptions(propagation_policy='Foreground'))
