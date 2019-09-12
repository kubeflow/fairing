from kubeflow import fairing
from kubeflow.fairing import http_utils
from kubeflow.fairing.constants import constants

EXPECTED_UA = constants.DEFAULT_USER_AGENT.format(VERSION=fairing.__version__)


class HTTPMock:
    def request(self, *args, **kwargs):
        if args and len(args) >= 4:
            return args[3]['user-agent']
        else:
            return kwargs['headers']['user-agent']


def test_configure_http_instance_empty_args():
    http = http_utils.configure_http_instance(HTTPMock())
    actual = http.request()
    assert actual == EXPECTED_UA


def test_configure_http_instance_args():
    http = http_utils.configure_http_instance(HTTPMock())
    actual = http.request("uri", "bla", "blahh", {'user-agent': "uatest"})
    assert actual == EXPECTED_UA + " uatest"


def test_configure_http_instance_kwargs():
    http = http_utils.configure_http_instance(HTTPMock())
    actual = http.request("uri", "bla", "blahh", headers={'user-agent': "uatest"})
    assert actual == EXPECTED_UA + " uatest"


def test_configure_http_instance_kwargs_no_ua():
    http = http_utils.configure_http_instance(HTTPMock())
    actual = http.request("uri", "bla", "blahh", headers={'not_ua': "uatest"})
    assert actual == EXPECTED_UA


def test_configure_http_instance_args_no_ua():
    http = http_utils.configure_http_instance(HTTPMock())
    actual = http.request("uri", "bla", "blahh", {'not_ua': "uatest"})
    assert actual == EXPECTED_UA
