import uuid

from kubernetes import client

from kubeflow.fairing import utils
from kubeflow.fairing.builders.cluster.context_source import ContextSourceInterface
from kubeflow.fairing.cloud import azure
from kubeflow.fairing.constants import constants


class StorageContextSource(ContextSourceInterface):
    """Azure storage context source"""
    def __init__(self, namespace=None, region=None,
                 resource_group_name=None, storage_account_name=None):
        self.namespace = namespace or utils.get_default_target_namespace()
        self.region = region or "NorthEurope"
        self.resource_group_name = resource_group_name or "fairing"
        self.storage_account_name = storage_account_name or "fairing{}".format(
            uuid.uuid4().hex[:17]
        )
        self.share_name = constants.AZURE_FILES_SHARED_FOLDER
        self.context_hash = None
        self.context_path = None

    def prepare(self, context_filename):  # pylint:disable=arguments-differ
        self.context_hash = utils.crc(context_filename)
        self.context_path = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        # Kaniko doesn't support Azure Storage yet.
        # So instead of uploading the context tar.gz file to Azure Storage
        # we are uploading the files in the context to a shared folder in Azure Files,
        # mounting the shared folder into the Kaniko pod,
        # and providing Kaniko with a local path to the files.
        azure_uploader = azure.AzureFileUploader(self.namespace)
        dir_name = "build_{}".format(self.context_hash)
        storage_account_name, storage_key = azure_uploader.upload_to_share(
            self.region,
            self.resource_group_name,
            self.storage_account_name,
            self.share_name,
            dir_name=dir_name,
            tar_gz_file_to_upload=context_filename)

        # This is the secret that we need to mount the shared folder into the Kaniko pod
        azure.create_storage_creds_secret(
            self.namespace, self.context_hash, storage_account_name, storage_key
        )

        # Local path to the files
        return "/mnt/azure/{}/".format(dir_name)


    def cleanup(self):
        azure.delete_storage_creds_secret(self.namespace, self.context_hash)

    def generate_pod_spec(self, image_name, push):  # pylint:disable=arguments-differ
        args = ["--dockerfile=Dockerfile",
                "--destination={}".format(image_name),
                "--context={}".format(self.context_path)]
        if not push:
            args.append("--no-push")
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='kaniko',
                image=constants.KANIKO_IMAGE,
                args=args,
            )],
            restart_policy='Never'
        )
