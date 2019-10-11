import json
import uuid
import logging

from kubernetes import client as k8s_client
from kubernetes.client.rest import ApiException

from kubeflow.fairing.constants import constants
from kubeflow.fairing.deployers.job.job import Job

logger = logging.getLogger(__name__)


class Serving(Job):
    """Serves a prediction endpoint using Kubernetes deployments and services"""

    def __init__(self, serving_class, namespace=None, runs=1, labels=None,
                 service_type="ClusterIP", pod_spec_mutators=None):
        """

        :param serving_class: the name of the class that holds the predict function.
        :param namespace: The k8s namespace where the it will be deployed.
        :param runs:
        :param labels: label for deployed service
        :param service_type: service type
        :param pod_spec_mutators: pod spec mutators (Default value = None)
        """
        super(Serving, self).__init__(namespace, runs,
                                      deployer_type=constants.SERVING_DEPLOPYER_TYPE,
                                      labels=labels)
        self.serving_class = serving_class
        self.service_type = service_type
        self.pod_spec_mutators = pod_spec_mutators or []

    def deploy(self, pod_spec):
        """deploy a seldon-core REST service

        :param pod_spec: pod spec for the service

        """
        self.job_id = str(uuid.uuid1())
        self.labels['fairing-id'] = self.job_id
        for fn in self.pod_spec_mutators:
            fn(self.backend, pod_spec, self.namespace)
        pod_template_spec = self.generate_pod_template_spec(pod_spec)
        pod_template_spec.spec.containers[0].command = ["seldon-core-microservice",
                                                        self.serving_class, "REST",
                                                        "--service-type=MODEL", "--persistence=0"]
        self.deployment_spec = self.generate_deployment_spec(pod_template_spec)
        self.service_spec = self.generate_service_spec()

        if self.output:
            api = k8s_client.ApiClient()
            job_output = api.sanitize_for_serialization(self.deployment_spec)
            logger.warning(json.dumps(job_output))
            service_output = api.sanitize_for_serialization(self.service_spec)
            logger.warning(json.dumps(service_output))

        v1_api = k8s_client.CoreV1Api()
        apps_v1 = k8s_client.AppsV1Api()
        self.deployment = apps_v1.create_namespaced_deployment(self.namespace, self.deployment_spec)
        self.service = v1_api.create_namespaced_service(self.namespace, self.service_spec)

        if self.service_type == "LoadBalancer":
            url = self.backend.get_service_external_endpoint(
                self.service.metadata.name, self.service.metadata.namespace,
                self.service.metadata.labels)
        else:
            # TODO(jlewi): The suffix won't always be cluster.local since
            # its configurable. Is there a way to get it programmatically?
            url = "http://{0}.{1}.svc.cluster.local:5000/predict".format(
                self.service.metadata.name, self.service.metadata.namespace)

        logging.info("Cluster endpoint: %s", url)
        return url

    def generate_deployment_spec(self, pod_template_spec):
        """generate deployment spec(V1Deployment)

        :param pod_template_spec: pod spec template

        """
        return k8s_client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=k8s_client.V1ObjectMeta(
                generate_name="fairing-deployer-",
                labels=self.labels,
            ),
            spec=k8s_client.V1DeploymentSpec(
                selector=k8s_client.V1LabelSelector(
                    match_labels=self.labels,
                ),
                template=pod_template_spec,
            )
        )

    def generate_service_spec(self):
        """ generate service spec(V1ServiceSpec)"""
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
                type=self.service_type,
            )
        )

    def delete(self):
        """ delete the deployed service"""
        v1_api = k8s_client.CoreV1Api()
        try:
            v1_api.delete_namespaced_service(self.service.metadata.name, #pylint:disable=no-value-for-parameter
                                             self.service.metadata.namespace)
            logger.info("Deleted service: {}/{}".format(self.service.metadata.namespace,
                                                        self.service.metadata.name))
        except ApiException as e:
            logger.error(e)
            logger.error("Not able to delete service: {}/{}".format(self.service.metadata.namespace,
                                                                    self.service.metadata.name))
        try:
            api_instance = k8s_client.ExtensionsV1beta1Api()
            del_opts = k8s_client.V1DeleteOptions(propagation_policy="Foreground")
            api_instance.delete_namespaced_deployment(self.deployment.metadata.name,
                                                      self.deployment.metadata.namespace,
                                                      body=del_opts)
            logger.info("Deleted deployment: {}/{}".format(self.deployment.metadata.namespace,
                                                           self.deployment.metadata.name))
        except ApiException as e:
            logger.error(e)
            logger.error("Not able to delete deployment: {}/{}"\
                         .format(self.deployment.metadata.namespace, self.deployment.metadata.name))
