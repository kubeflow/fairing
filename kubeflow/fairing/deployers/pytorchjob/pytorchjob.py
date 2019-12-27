import logging
from kubernetes import client as k8s_client

from kubeflow.pytorchjob import V1ReplicaSpec
from kubeflow.pytorchjob import V1PyTorchJob
from kubeflow.pytorchjob import V1PyTorchJobSpec

from kubeflow.fairing.constants import constants
from kubeflow.fairing.deployers.job.job import Job

logger = logging.getLogger(__name__)


class PyTorchJob(Job):
    """ Handle all the k8s' template building to create pytorch
        training job using Kubeflow PyTorch Operator"""
    def __init__(self, namespace=None, master_count=1, worker_count=1,
                 runs=1, job_name=constants.PYTORCH_JOB_DEFAULT_NAME,
                 stream_log=True, labels=None, pod_spec_mutators=None,
                 cleanup=False, annotations=None):
        """

        :param namespace: k8s namespace where the training's components
                will be deployed.
        :param worker_count: Number of worker pods created for training job.
        :param master_count: Number of master pods created for training job.
        :param runs: number of runs
        :param job_name: name of the job
        :param stream_log: stream the log from deployed pytorchjob
        :param labels: labels to be assigned to the training job
        :param pod_spec_mutators: pod spec mutators (Default value = None)
        :param cleanup: clean up deletes components after job finished
        :param annotations: annotations (Default value = None)
        """
        super(PyTorchJob, self).__init__(namespace, runs, job_name=job_name, stream_log=stream_log,
                                         deployer_type=constants.PYTORCH_JOB_DEPLOYER_TYPE,
                                         pod_spec_mutators=pod_spec_mutators, cleanup=cleanup,
                                         labels=labels, annotations=annotations)
        self.distribution = {
            'Master': master_count,
            'Worker': worker_count,
        }

    def create_resource(self):
        """ create a pytorchjob training"""
        self.created_pytorchjob = self.backend.create_pytorch_job(
            self.namespace, self.deployment_spec)
        return self.created_pytorchjob['metadata']['name']

    def generate_deployment_spec(self, pod_template_spec):
        """Returns a PyTorchJob template

        :param pod_template_spec: template spec for pod

        """
        self.set_container_name(pod_template_spec)

        pytorch_replica_specs = {}

        if self.distribution.get('Master', 0) > 0:
            Master = V1ReplicaSpec(
                replicas=self.distribution.get('Master', 0),
                template=pod_template_spec)
            pytorch_replica_specs.update(Master=Master)

        if self.distribution.get('Worker', 0) > 0:
            Worker = V1ReplicaSpec(
                replicas=self.distribution.get('Worker', 0),
                template=pod_template_spec)
            pytorch_replica_specs.update(Worker=Worker)

        pytorchjob = V1PyTorchJob(
            api_version=constants.PYTORCH_JOB_GROUP + "/" + \
                constants.PYTORCH_JOB_VERSION,
            kind=constants.PYTORCH_JOB_KIND,
            metadata=k8s_client.V1ObjectMeta(generate_name=self.job_name,
                                             labels=self.labels),
            spec=V1PyTorchJobSpec(pytorch_replica_specs=pytorch_replica_specs)
        )

        return pytorchjob

    def set_container_name(self, pod_template_spec):
        """Sets the name of the main container to `pytorch`.
            This is required for PytorchJob

        :param pod_template_spec: spec for pod template

        """
        pod_template_spec.spec.containers[0].name = 'pytorch'

    def get_logs(self):
        """ get logs"""
        name = self.created_pytorchjob['metadata']['name']
        namespace = self.created_pytorchjob['metadata']['namespace']

        labels = {
            'pytorch-replica-index': '0',
            'pytorch-replica-type': 'worker',
            'pytorch-job-name': name
        }
        self.backend.log(name, namespace, labels, container="pytorch")

        if self.cleanup:
            logger.warning("Cleaning up PyTorchJob {}...".format(name))
            self.backend.delete_pytorch_job(name, self.namespace)
