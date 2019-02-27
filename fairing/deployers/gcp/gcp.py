from fairing import utils
from fairing.deployers.deployer import DeployerInterface
from fairing.cloud.gcp import guess_project_name

from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from googleapiclient import errors

class GCPJob(DeployerInterface):
    """Handle submitting training job to GCP."""
    def __init__(self, project_id=None, region=None):
        self._project_id = project_id or guess_project_name()
        self._region = region or 'us-central1'

        self._ml = discovery.build('ml', 'v1')

    def deploy(self, pod_template_spec):
        """Deploys the training job"""
        # TODO: Update deploy interface to pass image directly instad of
        # PodTemplateSpec.
        # Retrieve image uri from pod template spec.
        image_uri = pod_template_spec.containers[0].image
        self._job_name = 'fairing_job_{}'.format(utils.random_tag())

        request_dict = {
            'jobId': self._job_name,
            'trainingInput': {
                'scaleTier': 'BASIC',
                'masterConfig': {
                    'imageUri': image_uri,
                },
                'region': self._region
            }
        }

        try:
            response = self._ml.projects().jobs().create(
                parent='projects/{}'.format(self._project_id),
                body=request_dict
            ).execute()
            print('Job submitted successfully.')
            self.get_logs()
        except errors.HttpError as err:
            print('There was an error submitting the job.')
            print(err._get_reason())

    def get_logs(self):
        """Streams the logs for the training job"""
        print('Access job logs at the following URL:')
        print('https://console.cloud.google.com/mlengine/jobs/{}?project={}'
              .format(self._job_name, self._project_id))
