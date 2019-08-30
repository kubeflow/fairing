import pytest
import random
from kubeflow import fairing
import httplib2
from google.cloud import storage

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
TEST_GCS_BUCKET = '{}-fairing'.format(GCS_PROJECT_ID)


@pytest.fixture
def temp_gcs_prefix():
    rnd_prefix = "fairing_test_assets_{}".format(random.randint(0, 10**9))
    yield rnd_prefix
    # delete all blobs with that prefix
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(TEST_GCS_BUCKET)
    for blob in bucket.list_blobs(prefix=rnd_prefix):
        print("deleting {}".format(blob.name))
        blob.delete()


@pytest.fixture
def httpmock():
    http = httplib2.Http()
    class HTTPMock:

        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            if args and len(args) >= 4:
                headers = args[3] or {}
            else:
                headers = kwargs.get('headers') or {}
            print(
                "HTTPMock url:{} user-agent:{}".format(args[0], headers.get('user-agent')))
            return http.request(*args, **kwargs)

    return HTTPMock
