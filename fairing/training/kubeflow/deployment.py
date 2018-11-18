from kubernetes import client as k8s_client

from ..native import deployment

class KubeflowDeployment(deployment.NativeDeployment):

    def deploy(self):
        self.backend.create_tf_job(self.namespace, self.job_spec)
    
    def generate_job(self, pod_template_spec):
        """Returns a TFJob template"""
        self.set_container_name(pod_template_spec)

        replica_spec = {}
        replica_spec['replicas'] = 1
        replica_spec['template'] = pod_template_spec

        spec = {} 
        spec['tfReplicaSpecs'] = {'Worker': replica_spec}

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
