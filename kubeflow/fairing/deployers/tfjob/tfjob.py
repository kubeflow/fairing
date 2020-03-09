import logging
from kubernetes import client as k8s_client

from kubeflow.tfjob import V1ReplicaSpec
from kubeflow.tfjob import V1TFJob
from kubeflow.tfjob import V1TFJobSpec

from kubeflow.fairing.constants import constants
from kubeflow.fairing.deployers.job.job import Job

logger = logging.getLogger(__name__)


class TfJob(Job):
    """ Handle all the k8s' template building to create tensorflow
        training job using Kubeflow TFOperator"""
    def __init__(self, namespace=None, worker_count=1, ps_count=0,
                 chief_count=1, runs=1, job_name=None, stream_log=True,
                 labels=None, pod_spec_mutators=None, cleanup=False, annotations=None,
                 config_file=None, context=None, client_configuration=None, persist_config=True):
        """

        :param namespace: k8s namespace where the training's components
                will be deployed.
        :param worker_count: Number of worker pods created for training job.
        :param ps_count: Number of parameter set pods created for training job.
        :param chief_count: Number of Chief pods created for training job.
        :param runs: number of runs
        :param job_name: name of the TFJob
        :param stream_log: stream the log from deployed tfjob
        :param labels: labels to be assigned to the training job
        :param pod_spec_mutators: pod spec mutators (Default value = None)
        :param cleanup: clean up deletes components after job finished
        :param annotations: annotations (Default value = None)
        :param config_file: kubeconfig file, defaults to ~/.kube/config. Note that for the case
               that the SDK is running in cluster and you want to operate in another remote
               cluster, user must set config_file to load kube-config file explicitly.
        :param context: kubernetes context
        :param client_configuration: The kubernetes.client.Configuration to set configs to.
        :param persist_config: If True, config file will be updated when changed
        """
        super(TfJob, self).__init__(namespace, runs, job_name=job_name, stream_log=stream_log,
                                    deployer_type=constants.TF_JOB_DEPLOYER_TYPE, labels=labels,
                                    pod_spec_mutators=pod_spec_mutators, cleanup=cleanup,
                                    annotations=annotations, config_file=config_file,
                                    context=context, client_configuration=client_configuration,
                                    persist_config=persist_config)
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

        tf_replica_specs = {}
        worker = V1ReplicaSpec(
            replicas=self.distribution['Worker'],
            template=pod_template_spec
        )
        tf_replica_specs = {"Worker": worker}

        if self.distribution.get('Chief', 0) > 0:
            chief = V1ReplicaSpec(
                replicas=self.distribution.get('Chief', 0),
                template=pod_template_spec)
            tf_replica_specs.update(Chief=chief)

        if self.distribution.get('PS', 0) > 0:
            ps = V1ReplicaSpec(
                replicas=self.distribution.get('PS', 0),
                template=pod_template_spec)
            tf_replica_specs.update(PS=ps)

        tfjob = V1TFJob(
            api_version=constants.TF_JOB_GROUP + "/" + constants.TF_JOB_VERSION,
            kind=constants.TF_JOB_KIND,
            metadata=k8s_client.V1ObjectMeta(name=self.job_name,
                                             generate_name=constants.TF_JOB_DEFAULT_NAME,
                                             labels=self.labels),
            spec=V1TFJobSpec(tf_replica_specs=tf_replica_specs)
        )

        return tfjob

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
