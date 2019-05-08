import fairing
import googleapiclient
import httplib2
from fairing.constants import constants

def configure_http_instance(http=None):
       if not http:
              http = httplib2.Http()
       
       request_orig = http.request
       user_agent = constants.DEFAULT_USER_AGENT.format(VERSION=fairing.__version__)
       # Reference: https://github.com/googleapis/google-api-python-client/blob/master/googleapiclient/http.py
       # The closure that will replace 'httplib2.Http.request'.
       def new_request(*args, **kwargs):
              """Modify the request headers to add the user-agent."""
              if args and len(args)>=4:
                     headers = args[3] or {}
                     headers['user-agent'] = user_agent
                     args[3] = headers
              else:
                     headers = kwargs.get('headers') or {}
                     headers['user-agent'] = user_agent
                     kwargs['headers'] = headers
              resp, content = request_orig(*args, **kwargs)
              return resp, content

       http.request = new_request
       return http
