TEMP_TAR_GZ_FILENAME = '/tmp/fairing.layer.tar.gz'
DEFAULT_IMAGE_NAME = 'fairing-job'
DEFAULT_BASE_IMAGE = 'gcr.io/kubeflow-images-public/fairing:dev'
DEFAULT_REGISTRY = 'index.docker.io'
DEFAULT_DEST_PREFIX = '/app/'

DEFAULT_CONTEXT_FILENAME = '/tmp/fairing.context.tar.gz'
DEFAULT_GENERATED_DOCKERFILE_FILENAME = '/tmp/Dockerfile'

GOOGLE_CREDS_ENV = 'GOOGLE_APPLICATION_CREDENTIALS'

GCP_CREDS_SECRET_NAME = 'user-gcp-sa'
AWS_CREDS_SECRET_NAME = 'aws-secret'
DOCKER_CREDS_SECRET_NAME = "docker-secret"

DEFAULT_USER_AGENT = 'kubeflow-fairing/{VERSION}'

# Job Constants
JOB_DEFAULT_NAME = 'fairing-job-'
JOB_DEPLOPYER_TYPE = 'job'

# Serving Constants
SERVING_DEPLOPYER_TYPE = 'serving'

#TFJob Constants
TF_JOB_GROUP = "kubeflow.org"
TF_JOB_KIND = "TFJob"
TF_JOB_PLURAL = "tfjobs"
TF_JOB_VERSION = "v1beta2"
TF_JOB_DEFAULT_NAME = 'fairing-tfjob-'
TF_JOB_DEPLOYER_TYPE = 'tfjob'

# KFServing constants
KFSERVING_GROUP = "serving.kubeflow.org"
KFSERVING_KIND = "KFService"
KFSERVING_PLURAL = "kfservices"
KFSERVING_VERSION = "v1alpha1"
KFSERVING_DEFAULT_NAME = 'fairing-kfserving-'
KFSERVING_DEPLOYER_TYPE = 'kfservice'
KFSERVING_CONTAINER_NAME = 'user-container'

# persistent volume claim constants
PVC_DEFAULT_MOUNT_PATH = '/mnt'
PVC_DEFAULT_VOLUME_NAME = 'fairing-volume-'
