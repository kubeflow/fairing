from google.cloud import storage
import os
import json


class GCSUploader(object):
    def __init__(self, credentials_file=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')):
        self.storage_client = storage.Client.from_service_account_json(credentials_file)

    def upload_to_bucket(self,
                        blob_name,
                        bucket_name,
                        file_to_upload):
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_to_upload)
        return "gs://{}/{}".format(bucket_name, blob_name)


def guess_project_name(credentials_file=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')):
    with open(credentials_file, 'rb') as f:
        data = f.read()
    parsed_creds_file = json.loads(data)
    return parsed_creds_file['project_id']