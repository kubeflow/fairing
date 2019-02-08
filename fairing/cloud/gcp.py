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


def guess_project_name(
        credentials_file=os.environ.get(constants.GOOGLE_CREDS_ENV)):
    if credentials_file is None:
        raise Exception("""No credential file provided.
        Please set GOOGLE_APPLICATION_CREDENTIALS environment variable to point
        to a credentials file.""")
    with open(credentials_file, 'r') as f:
        data = f.read()
    parsed_creds_file = json.loads(data)
    return parsed_creds_file['project_id']
