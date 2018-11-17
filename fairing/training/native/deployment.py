from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import logging

from kubernetes import client as k8s_client

from fairing import config
from fairing import utils
from fairing.training import base
from fairing.backend import kubernetes

logger = logging.getLogger(__name__)
DEFAULT_JOB_NAME = 'fairing-job'

class NativeDeployment(base.DeploymentInterface):
    """Handle all the template building for metaparticle api and calling mpclient

    Attributes:
        namespace: k8s namespace where the training's components 
            will be deployed.
        runs: Number of training(s) to be deployed. Hyperparameter search
            will generate multiple jobs.
    """

    def __init__(self, namespace, runs):
        if namespace is None:
            self.namespace = utils.get_default_target_namespace()
        else:
            self.namespace = namespace
        
        # Used as pod and job name
        self.name = "{}-{}".format(DEFAULT_JOB_NAME, utils.get_unique_tag())
        self.job_spec = None
        self.runs = runs

        self.builder = config.get_builder()
        self.backend = kubernetes.KubeManager()

    def execute(self):
        pod_spec = self.builder.generate_pod_spec()
        pod_template_spec = self.generate_pod_template_spec(pod_spec)

        #TODO:
        #pod_template_spec, tb_deployment = tensorboard.transform(pod_template_spec)
        #TODO:
        # pod_template_spec, pbt_deployment = pbt.transfort(pod_template_spec)

        self.job_spec = self.generate_job(pod_template_spec)

        #TODO: if needed, can be an extra validation step for the final template
        #self.validate(job_spec)

        # Actually build and push the image, or generate ConfigMaps
        self.builder.execute()
        self.deploy()
        logger.warn("Training(s) launched.")
        self.get_logs()
    
    def generate_pod_template_spec(self, pod_spec):
        """Generate a V1PodTemplateSpec initiazlied with correct metadata
            and with the provided pod_spec"""
        if not isinstance(pod_spec, k8s_client.V1PodSpec):
             raise TypeError('pod_spec must be a V1PodSpec, but got %s' 
                % type(pod_spec))

        return k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(name=self.name),
            spec=pod_spec)
        
    def generate_job(self, pod_template_spec):
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
            metadata=k8s_client.V1ObjectMeta(
                name=self.name
            ),
            spec=job_spec
        )

    def get_logs(self):
        self.backend.log(self.name, self.namespace)

    def deploy(self):
        """Handles communication with kubeclient to deploy 
            the component needed for the training"""
        self.backend.create_job(self.namespace, self.job_spec)