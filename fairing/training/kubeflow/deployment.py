from kubernetes import client as k8s_client

from ..native import deployment


class KubeflowDeployment(deployment.NativeDeployment):

    def __init__(self, namespace, job_name, runs, distribution):
        super(KubeflowDeployment, self).__init__(namespace, job_name, runs)
        self.distribution = distribution

    def deploy(self):
        self.backend.create_tf_job(self.namespace, self.job_spec)
    
    def generate_job(self, pod_template_spec):
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
        tf_job['apiVersion'] = 'kubeflow.org/v1alpha2'
        tf_job['metadata'] = k8s_client.V1ObjectMeta(name=self.name)
        tf_job['spec'] = spec

        return tf_job
    
    def set_container_name(self, pod_template_spec):
        """Sets the name of the main container to `tensorflow`.
            This is required for TfJobs"""
        pod_template_spec.spec.containers[0].name = 'tensorflow'

    def get_logs(self):
        selector='tf-replica-index=0,tf-replica-type=worker'
        self.backend.log(self.name, self.namespace, selector)
