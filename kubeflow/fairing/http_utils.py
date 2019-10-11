import httplib2
from kubeflow import fairing
from kubeflow.fairing.constants import constants

def configure_http_instance(http=None):
    """Configure http instance to modify the request headers to append or modify user-agent.

    :param http: Body of googleapiclient (Default value = None)
    :returns: object: Configurated http contents.

    """
    if not http:
        http = httplib2.Http()

    request_orig = http.request
    user_agent = constants.DEFAULT_USER_AGENT.format(VERSION=fairing.__version__)
    # Reference:
    # https://github.com/googleapis/google-api-python-client/blob/master/googleapiclient/http.py
    # The closure that will replace 'httplib2.Http.request'.
    def append_ua(headers):
        headers = headers or {}
        if 'user-agent' in headers:
            headers['user-agent'] = user_agent + " " + headers['user-agent']
        else:
            headers['user-agent'] = user_agent
        return headers
    def new_request(*args, **kwargs):
        """Modify the request headers to add the user-agent."""
        if args and len(args) >= 4:
            args = list(args)
            # args is a tuple so assignment is not possible
            args[3] = append_ua(args[3])
            args = tuple(args)
        else:
            kwargs['headers'] = append_ua(kwargs.get('headers'))
        return request_orig(*args, **kwargs)
    http.request = new_request
    return http
