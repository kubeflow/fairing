from kubernetes import client as k8s_client

from fairing.deployers import DeployerInterface
from fairing import kubernetes
from fairing.deployers import Job

class TfJob(Job):
    def __init__(self, namespace=None, worker_count=1, ps_count=0, runs=1):
        super(TfJob, self).__init__(namespace, runs)
        self.distribution = {
            'Worker': worker_count,
            'PS': ps_count,
            'Chief': 1
        }

    def create_resource(self):
        self.created_tfjob = self.backend.create_tf_job(self.namespace, self.deployment_spec)

    def generate_deployment_spec(self, pod_template_spec):
        """Returns a TFJob template"""
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
        tf_job['kind'] = 'TFJob'
        tf_job['apiVersion'] = 'kubeflow.org/' + kubernetes.TF_JOB_VERSION
        tf_job['metadata'] = k8s_client.V1ObjectMeta(generate_name="fairing-deployer-")
        tf_job['spec'] = spec

        return tf_job

    def set_container_name(self, pod_template_spec):
        """Sets the name of the main container to `tensorflow`.
            This is required for TfJobs"""
        pod_template_spec.spec.containers[0].name = 'tensorflow'

    def get_logs(self):
        labels = {
            'tf-replica-index': '0',
            'tf-replica-type': 'worker'
        }
        self.backend.log(self.created_tfjob.metadata.name, self.created_tfjob.metadata.namespace, labels)
