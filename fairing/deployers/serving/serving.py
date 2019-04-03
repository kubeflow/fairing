import json
import uuid
import logging

from kubernetes import client as k8s_client
from fairing.deployers.job.job import Job

logger = logging.getLogger(__name__)
DEPLOPYER_TYPE = 'serving'


class Serving(Job):
    """
    Serves a prediction endpoint using Kubernetes deployments and services 
    
    serving_class: the name of the class that holds the predict function.
    
    """
    def __init__(self, serving_class, namespace=None, runs=1, labels=None):
        super(Serving, self).__init__(namespace, runs, deployer_type=DEPLOPYER_TYPE, labels=labels)
        self.serving_class = serving_class
        
    def deploy(self, pod_spec):
        self.job_id = str(uuid.uuid1())
        self.labels['fairing-id'] = self.job_id
        pod_template_spec = self.generate_pod_template_spec(pod_spec)
        pod_template_spec.spec.containers[0].command = ["seldon-core-microservice", self.serving_class, "REST", "--service-type=MODEL", "--persistence=0"]
        self.deployment_spec = self.generate_deployment_spec(pod_template_spec)
        self.service_spec = self.generate_service_spec()
        
        if self.output:
            api = k8s_client.ApiClient()
            job_output = api.sanitize_for_serialization(self.deployment_spec)
            logger.warn(json.dumps(job_output))
            service_output = api.sanitize_for_serialization(self.service_spec)
            logger.warn(json.dumps(service_output))

        v1_api = k8s_client.CoreV1Api()
        apps_v1 = k8s_client.AppsV1Api()
        self.deployment = apps_v1.create_namespaced_deployment(self.namespace, self.deployment_spec)
        print("namespace",self.namespace)
        print("podspec", pod_spec)
        print("pod_template_spec", pod_template_spec)
        print("deployment_spec",self.deployment_spec)
        print("deployment.metadata", self.deployment.metadata)
        self.service = v1_api.create_namespaced_service(self.namespace, self.service_spec)

        logger.warn("Endpoint {} launched.".format(self.deployment.metadata.name))
        url = self.backend.get_service_external_endpoint(self.deployment.metadata.name, self.deployment.metadata.namespace, self.labels)
        return url

    def generate_deployment_spec(self, pod_template_spec):
        return k8s_client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=k8s_client.V1ObjectMeta(
                generate_name="fairing-deployer-"
            ),
            spec=k8s_client.V1DeploymentSpec(
                selector=k8s_client.V1LabelSelector(
                    match_labels=self.labels,
                ),
                template=pod_template_spec,
            )
        )
        
    def generate_service_spec(self):
        return k8s_client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=k8s_client.V1ObjectMeta(
                generate_name="fairing-service-",
                labels=self.labels,
            ),
            spec=k8s_client.V1ServiceSpec(
                selector=self.labels,
                ports=[k8s_client.V1ServicePort(
                    name="serving",
                    port=5000
                )],
                type="LoadBalancer",
            )
        )
