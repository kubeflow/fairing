import pytest
import random
import fairing
from google.cloud import storage

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
TEST_GCS_BUCKET = '{}-fairing'.format(GCS_PROJECT_ID)

@pytest.fixture
def temp_gcs_prefix():
    rnd_prefix = "fairing_test_assets_{}".format(random.randint(0, 10**9))
    yield rnd_prefix
    #delete all blobs with that prefix
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(TEST_GCS_BUCKET)
    for blob in bucket.list_blobs(prefix=rnd_prefix):
        print("deleting {}".format(blob.name))
        blob.delete()