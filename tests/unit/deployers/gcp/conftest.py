import os
import pytest
import httplib2

@pytest.fixture
def httpmock():
    http = httplib2.Http()
    class HTTPMock:

        def __init__(self, *args, **kwargs):
            pass
                     
        def request(self, *args, **kwargs):
            if args and len(args)>=4:
                headers = args[3] or {}
            else:
                headers = kwargs.get('headers') or {}
            print("HTTPMock url:{} user-agent:{}".format(args[0], headers.get('user-agent')))
            return http.request(*args, **kwargs)
    
    return HTTPMock
