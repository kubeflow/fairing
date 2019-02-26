import subprocess
import requests

from fairing import utils
from fairing.deployers.deployer import DeployerInterface
from fairing.cloud.gcp import guess_project_name

class GCPJob(DeployerInterface):
    """Handle submitting training job to GCP."""
    def __init__(self, project_id=None, region=None):
        self._project_id = project_id or guess_project_name()
        self._region = region or 'us-central1'

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

        auth = subprocess.run(['gcloud', 'auth', 'print-access-token'],
                              stdout=subprocess.PIPE).stdout[:-1].decode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(auth)
        }

        try:
            r = requests.post('https://ml.googleapis.com/v1/projects/{}/jobs'.format(self._project_id),
                              json=request_dict,
                              headers=headers)
            r.raise_for_status()
            print('Job submitted successfully.')
            print(r.json())
            self.get_logs()
        except requests.exceptions.RequestException as err:
            print('There was an error submitting the job.')
            print(err)

    def get_logs(self):
        """Streams the logs for the training job"""
        print('Access job logs at the following URL:')
        print('https://console.cloud.google.com/mlengine/jobs/{}?project={}'
              .format(self._job_name, self._project_id))
