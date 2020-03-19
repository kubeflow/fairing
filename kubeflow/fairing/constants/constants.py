import os

TEMP_TAR_GZ_FILENAME = '/tmp/fairing.layer.tar.gz'
DEFAULT_IMAGE_NAME = 'fairing-job'
DEFAULT_BASE_IMAGE = 'gcr.io/kubeflow-images-public/fairing:dev'
DEFAULT_REGISTRY = 'index.docker.io'
DEFAULT_DEST_PREFIX = '/app/'

DEFAULT_CONTEXT_FILENAME = '/tmp/fairing.context.tar.gz'
DEFAULT_GENERATED_DOCKERFILE_FILENAME = '/tmp/Dockerfile'

GOOGLE_CREDS_ENV = 'GOOGLE_APPLICATION_CREDENTIALS'
GCP_SERVICE_ACCOUNT_NAME = 'default-editor'

GCP_CREDS_SECRET_NAME = 'user-gcp-sa'
AWS_CREDS_SECRET_NAME = 'aws-secret'
DOCKER_CREDS_SECRET_NAME = "docker-secret"

# IBM Cloud Constants
IBM_COS_CREDS_FILE_NAME = 'cos_credentials'
IBM_COS_CREDS_SECRET_NAME = 'ibm-cos-creds'
IBM_COS_DEFAULT_ENDPOINT = 'https://s3.us.cloud-object-storage.appdomain.cloud'

# See https://github.com/kubeflow/website/issues/1033 for documentation about these secrets.
AZURE_CREDS_SECRET_NAME = 'azcreds'
AZURE_ACR_CREDS_SECRET_NAME = 'acrcreds'
# The secret containing credentials to access a specific storage account is dynamically generated
# by using Azure credentials to get those storage credentials.
AZURE_STORAGE_CREDS_SECRET_NAME_PREFIX = 'storage-credentials-'
AZURE_FILES_SHARED_FOLDER = 'fairing-builds'

DEFAULT_USER_AGENT = 'kubeflow-fairing/{VERSION}'

# Job Constants
JOB_DEFAULT_NAME = 'fairing-job-'
JOB_DEPLOPYER_TYPE = 'job'

# Serving Constants
SERVING_DEPLOPYER_TYPE = 'serving'

#TFJob Constants
TF_JOB_VERSION = os.environ.get('TF_JOB_VERSION', 'v1')
TF_JOB_GROUP = "kubeflow.org"
TF_JOB_KIND = "TFJob"
TF_JOB_PLURAL = "tfjobs"
TF_JOB_DEFAULT_NAME = 'fairing-tfjob-'
TF_JOB_DEPLOYER_TYPE = 'tfjob'

#PyTorchJob Constants
PYTORCH_JOB_VERSION = os.environ.get('PYTORCH_JOB_VERSION', 'v1')
PYTORCH_JOB_GROUP = "kubeflow.org"
PYTORCH_JOB_KIND = "PyTorchJob"
PYTORCH_JOB_PLURAL = "pytorchjobs"
PYTORCH_JOB_DEFAULT_NAME = 'fairing-pytorchjob-'
PYTORCH_JOB_DEPLOYER_TYPE = 'pytorchjob'

# KFServing constants
KFSERVING_GROUP = "serving.kubeflow.org"
KFSERVING_KIND = "InferenceService"
KFSERVING_PLURAL = "inferenceservices"
KFSERVING_VERSION = 'v1alpha2'
KFSERVING_DEFAULT_NAME = 'fairing-kfserving-'
KFSERVING_DEPLOYER_TYPE = 'kfservice'
KFSERVING_CONTAINER_NAME = 'user-container'

# persistent volume claim constants
PVC_DEFAULT_MOUNT_PATH = '/mnt'
PVC_DEFAULT_VOLUME_NAME = 'fairing-volume-'

# Kaniko Constants
KANIKO_IMAGE = 'gcr.io/kaniko-project/executor:v0.14.0'

#Fairing Logging Constants
FAIRING_LOG_LEVEL = os.environ.get('FAIRING_LOG_LEVEL', 'INFO').upper()
FAIRING_LOG_FORMAT = '%(levelname)s|%(asctime)s|%(pathname)s|%(lineno)d| %(message)s'
FAIRING_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
