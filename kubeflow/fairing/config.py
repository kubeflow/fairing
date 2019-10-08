from kubeflow.fairing.preprocessors.base import BasePreProcessor
from kubeflow.fairing.preprocessors.converted_notebook import ConvertNotebookPreprocessor
from kubeflow.fairing.preprocessors.full_notebook import FullNotebookPreProcessor
from kubeflow.fairing.preprocessors.function import FunctionPreProcessor

from kubeflow.fairing.builders.append.append import AppendBuilder
from kubeflow.fairing.builders.docker.docker import DockerBuilder
from kubeflow.fairing.builders.cluster.cluster import ClusterBuilder

from kubeflow.fairing.deployers.job.job import Job
from kubeflow.fairing.deployers.serving.serving import Serving
from kubeflow.fairing.deployers.tfjob.tfjob import TfJob
from kubeflow.fairing.deployers.gcp.gcp import GCPJob
from kubeflow.fairing.deployers.kfserving.kfserving import KFServing

from kubeflow.fairing.notebook import notebook_util

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
        """ reset the preprocessor, builder_name and deployer name"""
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
        """

        :param name: preprocessor name(Default value = None)

        """
        self._preprocessor_name = name
        self._preprocessor_kwargs = kwargs

    def get_preprocessor(self):
        """ get the preprocessor"""
        fn = preprocessor_map.get(self._preprocessor_name)
        if fn is None:
            raise Exception('Preprocessor name not found: {}\nAvailable preprocessor: {}'.format(
                self._preprocessor_name, list(preprocessor_map.keys())))
        return fn(**self._preprocessor_kwargs)

    def set_builder(self, name=DEFAULT_BUILDER, **kwargs):
        """set the builder

        :param name: builder name (Default value = DEFAULT_BUILDER)

        """
        self._builder_name = name
        self._builder_kwargs = kwargs

    def get_builder(self, preprocessor):
        """get the builder

        :param preprocessor: preprocessor function

        """
        fn = builder_map.get(self._builder_name)
        if fn is None:
            raise Exception('Builder name not found: {}\nAvailable builder: {}'.format(
                self._builder_name, list(builder_map.keys())))
        return fn(preprocessor=preprocessor, **self._builder_kwargs)

    def set_deployer(self, name=DEFAULT_DEPLOYER, **kwargs):
        """set the deployer

        :param name: deployer name (Default value = DEFAULT_DEPLOYER)

        """
        self._deployer_name = name
        self._deployer_kwargs = kwargs

    def get_deployer(self):
        """ get deployer"""
        fn = deployer_map.get(self._deployer_name)
        if fn is None:
            raise Exception('Deployer name not found: {}\nAvailable deployer: {}'.format(
                self._deployer_name, list(deployer_map.keys())))
        return fn(**self._deployer_kwargs)

    def run(self):
        """ run the pipeline for job"""
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
        """deploy the job

        :param pod_spec: pod spec of the job

        """
        return self.get_deployer().deploy(pod_spec)

    def fn(self, fn):
        """function

        :param fn: return func that set the preprocessorr and run

        """
        def ret_fn():
            """ return the function"""
            self.set_preprocessor('function', function_obj=fn)
            self.run()
        return ret_fn


config = Config()
