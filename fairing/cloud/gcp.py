import google.auth
from google.cloud import storage
from fairing.constants import constants

import os
import json


class GCSUploader(object):
    def __init__(
            self,
            credentials_file=os.environ.get(constants.GOOGLE_CREDS_ENV)):
        self.storage_client = storage. \
            Client.from_service_account_json(credentials_file)

    def upload_to_bucket(self,
                         blob_name,
                         bucket_name,
                         file_to_upload):
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_to_upload)
        return "gs://{}/{}".format(bucket_name, blob_name)


def guess_project_name(credentials_file=None):
    # Check credentials file if provided
    if credentials_file is not None:
        with open(credentials_file, 'r') as f:
            data = f.read()
        parsed_creds_file = json.loads(data)
        return parsed_creds_file['project_id']

    # Use the google.auth library to retrieve credentials. Checks the following
    # locations in order:
    # 1. GOOGLE_APPLICATION_CREDENTIALS environment variable
    # 2. Google Cloud SDK (gcloud)
    # 3. App Engine Identity service
    # 4. Compute Engine Metadata service
    credentials, project_id = google.auth.default()

    if project_id is None:
        raise Exception('Could not determine project id.')

    return project_id
