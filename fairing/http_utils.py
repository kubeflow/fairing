import fairing
import googleapiclient
import httplib2
from fairing.constants import constants

def configure_http_instance(http=None):
       if not http:
              http = httplib2.Http()
       
       request_orig = http.request
       # Reference: https://github.com/googleapis/google-api-python-client/blob/master/googleapiclient/http.py
       # The closure that will replace 'httplib2.Http.request'.
       def new_request(uri, method='GET', body=None, headers=None,
                     redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                     connection_type=None):
              """Modify the request headers to add the user-agent."""
              if headers is None:
                     headers = {}
              headers['user-agent'] = constants.DEFAULT_USER_AGENT.format(VERSION=fairing.__version__)
              resp, content = request_orig(uri, method, body, headers,
                                   redirections, connection_type)
              return resp, content

       http.request = new_request
       return http
