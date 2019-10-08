import logging
from kubernetes import client as k8s_client

from kubeflow.fairing.constants import constants
from kubeflow.fairing.deployers.job.job import Job

logger = logging.getLogger(__name__)


class TfJob(Job):
    """ Handle all the k8s' template building to create tensorflow
        training job using Kubeflow TFOperator"""
    def __init__(self, namespace=None, worker_count=1, ps_count=0,
                 chief_count=1, runs=1, job_name=constants.TF_JOB_DEFAULT_NAME, stream_log=True,
                 labels=None, pod_spec_mutators=None, cleanup=False):
        """

        :param namespace: k8s namespace where the training's components
                will be deployed.
        :param worker_count: Number of worker pods created for training job.
        :param ps_count: Number of parameter set pods created for training job.
        :param chief_count: Number of Chief pods created for training job.
        :param runs: number of runs
        :param job_name: name of the job
        :param stream_log: stream the log from deployed tfjob
        :param labels: labels to be assigned to the training job
        :param pod_spec_mutators: pod spec mutators (Default value = None)
        :param cleanup: clean up deletes components after job finished
        """
        super(TfJob, self).__init__(namespace, runs, job_name=job_name, stream_log=stream_log,
                                    deployer_type=constants.TF_JOB_DEPLOYER_TYPE, labels=labels,
                                    pod_spec_mutators=pod_spec_mutators, cleanup=cleanup)
        self.distribution = {
            'Worker': worker_count,
            'PS': ps_count,
            'Chief': chief_count
        }

    def create_resource(self):
        """ create a tfjob training"""
        self.created_tfjob = self.backend.create_tf_job(self.namespace, self.deployment_spec)
        return self.created_tfjob['metadata']['name']

    def generate_deployment_spec(self, pod_template_spec):
        """Returns a TFJob template

        :param pod_template_spec: template spec for pod

        """
        self.set_container_name(pod_template_spec)

        worker_replica_spec = {}
        worker_replica_spec['replicas'] = self.distribution['Worker']
        worker_replica_spec['template'] = pod_template_spec

        ps_replica_spec = {}
        ps_replica_spec['replicas'] = self.distribution.get('PS', 0)
        ps_replica_spec['template'] = pod_template_spec

        chief_replica_spec = {}
        chief_replica_spec['replicas'] = self.distribution.get('Chief', 0)
        chief_replica_spec['template'] = pod_template_spec

        spec = {}
        spec['tfReplicaSpecs'] = {}
        spec['tfReplicaSpecs']['Worker'] = worker_replica_spec
        if chief_replica_spec['replicas'] > 0:
            spec['tfReplicaSpecs']['Chief'] = chief_replica_spec
        if ps_replica_spec['replicas'] > 0:
            spec['tfReplicaSpecs']['PS'] = ps_replica_spec

        tf_job = {}
        tf_job['kind'] = constants.TF_JOB_KIND
        tf_job['apiVersion'] = 'kubeflow.org/' + constants.TF_JOB_VERSION
        tf_job['metadata'] = k8s_client.V1ObjectMeta(generate_name=self.job_name,
                                                     labels=self.labels)
        tf_job['spec'] = spec

        return tf_job

    def set_container_name(self, pod_template_spec):
        """Sets the name of the main container to `tensorflow`.
            This is required for TfJobs

        :param pod_template_spec: spec for pod template

        """
        pod_template_spec.spec.containers[0].name = 'tensorflow'

    def get_logs(self):
        """ get logs"""
        name = self.created_tfjob['metadata']['name']
        namespace = self.created_tfjob['metadata']['namespace']

        labels = {
            'tf-replica-index': '0',
            'tf-replica-type': 'worker',
            'tf-job-name': name
        }
        self.backend.log(name, namespace, labels, container="tensorflow")

        if self.cleanup:
            logger.warning("Cleaning up TFJob {}...".format(name))
            self.backend.delete_tf_job(name, self.namespace)
