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

DEFAULT_USER_AGENT = 'kubeflow-fairing/{VERSION}'

# KFServing constants
KFSERVING_GROUP = "serving.kubeflow.org"
KFSERVING_KIND = "KFService"
KFSERVING_PLURAL = "kfservices"
KFSERVING_VERSION = "v1alpha1"
KFSERVING_DEFAULT_NAME = 'fairing-kfserving-'
KFSERVING_DEPLOYER_TYPE = 'kfservice'
KFSERVING_CONTAINER_NAME = 'user-container'