from googleapiclient import discovery
from googleapiclient import errors

from kubeflow.fairing.deployers.deployer import DeployerInterface
from kubeflow.fairing.cloud.gcp import guess_project_name
from kubeflow.fairing import http_utils


# TODO: Implement predict and delete methods.
class GCPServingDeployer(DeployerInterface):
    """Handle deploying a trained model to GCP."""
    def __init__(self, model_dir, model_name, version_name, project_id=None,
                 **deploy_kwargs):
        self._project_id = project_id or guess_project_name()

        self._model_dir = model_dir
        self._model_name = model_name
        self._version_name = version_name
        self._deploy_kwargs = deploy_kwargs
        self._ml = discovery.build('ml', 'v1')
        self._ml._http = http_utils.configure_http_instance(self._ml._http) #pylint:disable=protected-access

        # Set default deploy kwargs
        if 'runtime_version' not in self._deploy_kwargs:
            self._deploy_kwargs['runtime_version'] = '1.13'
        if 'python_version' not in self._deploy_kwargs:
            self._deploy_kwargs['python_version'] = '3.5'

    def deploy(self, pod_template_spec):
        """Deploys the model to Cloud ML Engine.

        :param pod_template_spec: pod spec template of training job

        """
        # Check if the model exists
        try:
            res = self._ml.projects().models().get(
                name='projects/{}/models/{}'.format(self._project_id, self._model_name)
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
                model_body = {'name': self._model_name}
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
            version_body['name'] = self._version_name
            version_body['deploymentUri'] = self._model_dir

            res = self._ml.projects().models().versions().create(
                parent='projects/{}/models/{}'.format(
                    self._project_id, self._model_name),
                body=version_body
            ).execute()
        except errors.HttpError as err:
            print('Error creating the version: {}'.format(err))
            return

        print('Version submitted successfully. Access the version at the following URL:')
        print('https://console.cloud.google.com/mlengine/models/{}/versions/{}?project={}'.format(
            self._model_name, self._version_name, self._project_id))

    def get_logs(self):
        """ abstract get log"""
        raise NotImplementedError('Retrieving logs is not supported for the GCP Serving deployer.')
