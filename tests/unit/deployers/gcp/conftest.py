import os
import pytest
import httplib2


@pytest.fixture
def ml_api_spec_response():
    """
    Creates a response simillar to calling google discover endpoint.
    api_spec.json contains the api spec for gcp ml service (AI Platform)
    """
    path = os.path.join(os.path.dirname(__file__), "api_spec.json")
    with open(path,'r') as f:
        api_spec = f.read()
        res = httplib2.Response(
                {
                    "content-type": "text/plain",
                    "status": "200",
                    "content-length": len(api_spec),
                }
            )
        return res, api_spec
