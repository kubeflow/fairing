from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import logging
logging.basicConfig(format='%(message)s')

from fairing import preprocessors
from fairing import builders
from fairing import deployers

from fairing.notebook import notebook_util

DEFAULT_PREPROCESSOR='python'
DEFAULT_BUILDER='append'
DEFAULT_DEPLOYER='job'

preprocessor_map = {
    'python': preprocessors.BasePreProcessor,
    'notebook': preprocessors.ConvertNotebookPreprocessor,
    'full_notebook': preprocessors.FullNotebookPreProcessor,
}

builder_map = {
    'append': builders.AppendBuilder,
    'docker': builders.DockerBuilder,
    'cluster': builders.ClusterBuilder,
}

deployer_map = {
    'job': deployers.Job,
    'tfjob': deployers.TfJob
}


class Config(object):
    def __init__(self):
        self._preprocessor = None
        self._builder = None
        self._deployer = None
        self._model = None

    def set_preprocessor(self, name=None, **kwargs):
        if name is None:
            if notebook_util.is_in_notebook():
                name = 'notebook'
            else:
                name = DEFAULT_PREPROCESSOR
        preprocessor = preprocessor_map.get(name)
        self._preprocessor = preprocessor(**kwargs)
    
    def get_preprocessor(self):
        return self._preprocessor

    def set_builder(self, name=DEFAULT_BUILDER, **kwargs):
        if self._preprocessor is None:
            self.set_preprocessor()
        builder = builder_map.get(name)
        self._builder = builder(preprocessor=self.get_preprocessor(), **kwargs)
        if not isinstance(self._builder, builders.BuilderInterface):
            raise TypeError(
                'builder must be a BuilderInterface, but got %s' 
                % type(self._builder))
    
    def get_builder(self):
        if self._builder is None:
            self.set_builder()
        return self._builder
        
    def set_deployer(self, name=DEFAULT_DEPLOYER, **kwargs):
        deployer = deployer_map.get(name)
        self._deployer = deployer(**kwargs)
        if not isinstance(self._deployer, deployers.DeployerInterface):
            raise TypeError(
                'backend must be a DeployerInterface, but got %s' 
                % type(self._deployer))

    def get_deployer(self):
        if self._deployer is None:
            self.set_deployer()
        return self._deployer
        
    def set_model(self, model):
        self._model = model
    
    def get_model(self):
        return self._model

    def run(self):
        self.get_builder().build()
        pod_spec = self._builder.generate_pod_spec()
        self.get_deployer().deploy(pod_spec)


config = Config()
