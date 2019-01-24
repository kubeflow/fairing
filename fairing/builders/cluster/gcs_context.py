from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import os

from fairing.cloud import gcp
from fairing import utils
from fairing.kubernetes import client, KubeManager
from fairing.builders.cluster.context_source import ContextSourceInterface

class GCSContextSource(ContextSourceInterface):
    def __init__(self,
                 gcp_project=gcp.guess_project_name(),
                 credentials_file=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                 namespace='default'):
                self.gcp_project = gcp_project
                self.credentials_file = credentials_file
                self.manager = KubeManager()
                self.namespace = namespace

    def prepare(self, context_filename):
        self.uploaded_context_url = self.upload_context(context_filename)
        self.created_secret = self.create_secret()

    def upload_context(self, context_filename):
        gcs_uploader = gcp.GCSUploader()
        context_hash = utils.crc(context_filename)
        return gcs_uploader.upload_to_bucket(
                    bucket_name=self.gcp_project,
                    blob_name='fairing_builds/' + context_hash,
                    file_to_upload=context_filename)
        
    def create_secret(self):
        with open(self.credentials_file, 'r') as f:
            secret_data = f.read()

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(
                generate_name='fairing-kaniko-secret-',
                namespace=self.namespace,
                labels={'fairing-builder-kaniko': 'secret'}
            ),
            string_data={'kaniko-secret': secret_data}
        )

        return client.CoreV1Api().create_namespaced_secret(self.namespace, secret)

    def cleanup(self):
        client.CoreV1Api().delete_namespaced_secret(
            self.created_secret.metadata.name,
            self.created_secret.metadata.namespace,
            client.V1DeleteOptions())

    def generate_pod_spec(self, image_name):
        return client.V1PodSpec(
                containers=[client.V1Container(
                    name='kaniko',
                    image='gcr.io/kaniko-project/executor:v0.7.0',
                    volume_mounts=[client.V1VolumeMount(
                        name='kaniko-secret',
                        mount_path='/secret',
                    )],
                    args=["--dockerfile=Dockerfile",
                          "--destination=" + image_name,
                          "--context=" + self.uploaded_context_url],
                    env=[client.V1EnvVar(
                        name='GOOGLE_APPLICATION_CREDENTIALS',
                        value='/secret/kaniko-secret',
                    )],
                )],
                volumes=[client.V1Volume(
                    name='kaniko-secret',
                    secret=client.V1SecretVolumeSource(
                        secret_name=self.created_secret.metadata.name,
                    ),
                )],
                restart_policy='Never'
            )