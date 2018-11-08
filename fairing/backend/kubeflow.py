import logging
from fairing.kubeclient import KubeClient
from fairing.backend.native import NativeBackend

logger = logging.getLogger('fairing')

# This class can contain any specifities related to kubeflow services.
# i.e. if kubeflow provides a TensorBoard CRD we could use it here
class KubeflowBackend(NativeBackend):
    def __init__(self):
        self.client = KubeClient()

    def stream_logs(self, image_name, image_tag, namespace):
        chief = '%s-chief-0' % image_tag
        logger.info('You can check the logs for your job by running '
                    '"kubectl logs -f %s"' % chief)
        self.client.logs(chief, namespace)
        logger.info('Done streaming logs ')

    def cleanup(self, image_name, image_tag, namespace):
        self.client.cleanup(image_tag, namespace)

    def get_client(self):
        return self.client