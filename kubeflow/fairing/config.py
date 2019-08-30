from .preprocessors.base import BasePreProcessor
from .preprocessors.converted_notebook import ConvertNotebookPreprocessor
from .preprocessors.full_notebook import FullNotebookPreProcessor
from .preprocessors.function import FunctionPreProcessor

from .builders.append.append import AppendBuilder
from .builders.docker.docker import DockerBuilder
from .builders.cluster.cluster import ClusterBuilder

from .deployers.job.job import Job
from .deployers.serving.serving import Serving
from .deployers.tfjob.tfjob import TfJob
from .deployers.gcp.gcp import GCPJob
from .deployers.kfserving.kfserving import KFServing

from .notebook import notebook_util

import logging
logging.basicConfig(format='%(message)s')

DEFAULT_PREPROCESSOR = 'python'
DEFAULT_BUILDER = 'append'
DEFAULT_DEPLOYER = 'job'

preprocessor_map = {
    'python': BasePreProcessor,
    'notebook': ConvertNotebookPreprocessor,
    'full_notebook': FullNotebookPreProcessor,
    'function': FunctionPreProcessor,
}

builder_map = {
    'append': AppendBuilder,
    'docker': DockerBuilder,
    'cluster': ClusterBuilder,
}

deployer_map = {
    'job': Job,
    'tfjob': TfJob,
    'gcp': GCPJob,
    'serving': Serving,
    'kfserving': KFServing,
}


class Config(object):
    def __init__(self):
        self.reset()

    def reset(self):
        if notebook_util.is_in_notebook():
            self._preprocessor_name = 'notebook'
        else:
            self._preprocessor_name = DEFAULT_PREPROCESSOR
        self._preprocessor_kwargs = {}

        self._builder_name = DEFAULT_BUILDER
        self._builder_kwargs = {}

        self._deployer_name = DEFAULT_DEPLOYER
        self._deployer_kwargs = {}

    def set_preprocessor(self, name=None, **kwargs):
        self._preprocessor_name = name
        self._preprocessor_kwargs = kwargs

    def get_preprocessor(self):
        fn = preprocessor_map.get(self._preprocessor_name)
        if fn is None:
            raise Exception('Preprocessor name not found: {}\nAvailable preprocessor: {}'.format(
                self._preprocessor_name, list(preprocessor_map.keys())))
        return fn(**self._preprocessor_kwargs)

    def set_builder(self, name=DEFAULT_BUILDER, **kwargs):
        self._builder_name = name
        self._builder_kwargs = kwargs

    def get_builder(self, preprocessor):
        fn = builder_map.get(self._builder_name)
        if fn is None:
            raise Exception('Builder name not found: {}\nAvailable builder: {}'.format(
                self._builder_name, list(builder_map.keys())))
        return fn(preprocessor=preprocessor, **self._builder_kwargs)

    def set_deployer(self, name=DEFAULT_DEPLOYER, **kwargs):
        self._deployer_name = name
        self._deployer_kwargs = kwargs

    def get_deployer(self):
        fn = deployer_map.get(self._deployer_name)
        if fn is None:
            raise Exception('Deployer name not found: {}\nAvailable deployer: {}'.format(
                self._deployer_name, list(deployer_map.keys())))
        return fn(**self._deployer_kwargs)

    def run(self):
        preprocessor = self.get_preprocessor()
        logging.info("Using preprocessor: %s", preprocessor)
        builder = self.get_builder(preprocessor)
        logging.info("Using builder: %s", builder)
        deployer = self.get_deployer()
        logging.info("Using deployer: %s", builder)

        builder.build()
        pod_spec = builder.generate_pod_spec()
        deployer.deploy(pod_spec)

        return preprocessor, builder, deployer

    def deploy(self, pod_spec):
        return self.get_deployer().deploy(pod_spec)

    def fn(self, fn):
        def ret_fn():
            self.set_preprocessor('function', function_obj=fn)
            self.run()
        return ret_fn


config = Config()
