from fairing import utils
from fairing.deployers.deployer import DeployerInterface
from fairing.cloud.gcp import guess_project_name

from googleapiclient import discovery
from googleapiclient import errors

# TODO: Integrate with DeployerInterface
class GCPServingDeployer:
    """Handle deploying a trained model to GCP."""
    def __init__(self, project_id=None):
        self._project_id = project_id or guess_project_name()
        self._ml = discovery.build('ml', 'v1')

        # Set default deploy kwargs
        self._deploy_kwargs = {
            'runtime_version': '1.12',
            'python_version': '3.5'
        }

    def deploy(self, model_dir, model_name, version_name, **deploy_kwargs):
        """Deploys the model to Cloud ML Engine."""
        self._deploy_kwargs.update(deploy_kwargs)

        # Check if the model exists
        try:
            res = self._ml.projects().models().get(
                name='projects/{}/models/{}'.format(self._project_id, model_name)
            ).execute()
        except errors.HttpError as err:
            if err.resp['status'] == '404':
                # Model not found
                res = None
            else:
                # Other error with the command
                print('Error retrieving the model: {}'.format(err))
                return

        if res is None:
            # Create the model
            try:
                model_body = {'name': model_name}
                res = self._ml.projects().models().create(
                    parent='projects/{}'.format(self._project_id),
                    body=model_body
                ).execute()
            except errors.HttpError as err:
                print('Error creating the model: {}'.format(err))
                return

        # Create the version
        try:
            version_body = self._deploy_kwargs
            version_body['name'] = version_name
            version_body['deploymentUri'] = model_dir

            res = self._ml.projects().models().versions().create(
                parent='projects/{}/models/{}'.format(
                    self._project_id, model_name),
                body=version_body
            ).execute()
        except errors.HttpError as err:
            print('Error creating the version: {}'.format(err))
            return

        print('Version submitted successfully. Access the version at the following URL:')
        print('https://console.cloud.google.com/mlengine/models/{}/versions/{}?project={}'.format(
            model_name, version_name, self._project_id))

