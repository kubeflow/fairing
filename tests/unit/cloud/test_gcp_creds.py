import json
from unittest.mock import patch

from kubeflow.fairing.cloud.gcp import guess_project_name

# Test guess_project_name with application default credentials.


def test_guess_project_name_application_default_file(tmp_path):
    creds_file = tmp_path / 'credentials'
    project_id = 'test_project'

    with creds_file.open('w') as f:
        json.dump({
            'project_id': project_id
        }, f)

    assert guess_project_name(str(creds_file)) == project_id

# Test that guess_project_name returns the project returned by
# google.auth.default when no input file is provided.


def test_guess_project_name_google_auth(tmp_path): #pylint:disable=unused-argument
    project_id = 'test_project'

    with patch('google.auth.default', return_value=(None, project_id)):
        assert guess_project_name() == project_id
