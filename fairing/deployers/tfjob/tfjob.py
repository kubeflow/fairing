from kubernetes import client as k8s_client

from fairing.deployers.job.job import Job
from fairing.kubernetes.manager import TF_JOB_VERSION
DEFAULT_JOB_NAME = 'fairing-tfjob-'


class TfJob(Job):
    def __init__(self, namespace=None, worker_count=1, ps_count=0,
                 chief_count=1, runs=1, job_name=DEFAULT_JOB_NAME, stream_log=True,
                 mount_credentials=False):
        super(TfJob, self).__init__(namespace, runs, job_name=job_name, stream_log=stream_log)
        self.distribution = {
            'Worker': worker_count,
            'PS': ps_count,
            'Chief': chief_count
        }
        self.mount_credentials = mount_credentials

    def create_resource(self):
        self.created_tfjob = self.backend.create_tf_job(self.namespace, self.deployment_spec)
        return self.created_tfjob['metadata']['name']

    def generate_deployment_spec(self, pod_template_spec):
        """Returns a TFJob template"""
        self.set_container_name(pod_template_spec)

        # TODO: Extract config options into a global config set, in order to
        # enable platform-specific options.
        if self.mount_credentials:
            # Set appropriate secrets and volumes to enable kubeflow-user service
            # account.
            env_var = k8s_client.V1EnvVar(
                name='GOOGLE_APPLICATION_CREDENTIALS',
                value='/etc/secrets/user-gcp-sa.json')
            if pod_template_spec.spec.containers[0].env:
                pod_template_spec.spec.containers[0].env.append(env_var)
            else:
                pod_template_spec.spec.containers[0].env = [env_var]

            volume_mount = k8s_client.V1VolumeMount(
                name='user-gcp-sa', mount_path='/etc/secrets', read_only=True)
            if pod_template_spec.spec.containers[0].volume_mounts:
                pod_template_spec.spec.containers[0].volume_mounts.append(volume_mount)
            else:
                pod_template_spec.spec.containers[0].volume_mounts = [volume_mount]

            volume = k8s_client.V1Volume(
                name='user-gcp-sa',
                secret=k8s_client.V1SecretVolumeSource(secret_name='user_gcp_sa'))
            if pod_template_spec.spec.volumes:
                pod_template_spec.spec.volumes.append(volume)
            else:
                pod_template_spec.spec.volumes = [volume]

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
        tf_job['apiVersion'] = 'kubeflow.org/' + TF_JOB_VERSION
        tf_job['metadata'] = k8s_client.V1ObjectMeta(generate_name=self.job_name)
        tf_job['spec'] = spec

        return tf_job

    def set_container_name(self, pod_template_spec):
        """Sets the name of the main container to `tensorflow`.
            This is required for TfJobs"""
        pod_template_spec.spec.containers[0].name = 'tensorflow'

    def get_logs(self):
        name = self.created_tfjob['metadata']['name']
        namespace = self.created_tfjob['metadata']['namespace']

        labels = {
            'tf-replica-index': '0',
            'tf-replica-type': 'worker',
            'tf_job_name=': name
        }
        self.backend.log(name, namespace, labels)
