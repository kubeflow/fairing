from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import logging
import json

from kubernetes import client as k8s_client

import fairing
from fairing import utils

from fairing.deployers import DeployerInterface
from fairing import kubernetes

logger = logging.getLogger(__name__)
DEFAULT_JOB_NAME = 'fairing-job'

class Job(DeployerInterface):
    """Handle all the k8s' template building for a training 
    Attributes:
        namespace: k8s namespace where the training's components 
            will be deployed.
        runs: Number of training(s) to be deployed. Hyperparameter search
            will generate multiple jobs.
    """

    def __init__(self, namespace=None, runs=1, output=None, labels={'fairing-deployer': 'job'}):
        if namespace is None:
            self.namespace = utils.get_default_target_namespace()
        else:
            self.namespace = namespace
        
        # Used as pod and job name
        self.deployment_spec = None
        self.runs = runs
        self.output = output
        self.labels = labels
        
        self.backend = kubernetes.KubeManager()

    def deploy(self, pod_spec):
        pod_template_spec = self.generate_pod_template_spec(pod_spec)
        self.deployment_spec = self.generate_deployment_spec(pod_template_spec)
        if self.output:
            api = k8s_client.ApiClient()
            job_output = api.sanitize_for_serialization(self.deployment_spec)
            print(json.dumps(job_output))

        self.create_resource()
        logger.warn("Training(s) launched.")
        self.get_logs()
        
    def create_resource(self):
        self._created_job = self.backend.create_job(self.namespace, self.deployment_spec)

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
                generate_name="fairing-deployer-"
            ),
            spec=job_spec
        )

    def get_logs(self):
        self.backend.log(self._created_job.metadata.name, self._created_job.metadata.namespace, self.labels)
