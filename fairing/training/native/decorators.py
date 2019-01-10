from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from future import standard_library
standard_library.install_aliases()

import logging

from fairing.training import base
from .deployment import NativeDeployment
from .runtime import BasicNativeRuntime

logger = logging.getLogger(__name__)


class Training(base.TrainingDecoratorInterface):
    """A simple Kubernetes training.
    
    Args:
        namespace {string} -- (optional) here the training should be deployed
    """

    def __init__(self, namespace=None, job_name=None):
        self.job_name = job_name
        self.namespace = namespace
        self.runs = 1
    
    def _validate(self, user_object):
        """TODO: Verify that the training conforms to what is expected from 
            a simple training. (probably not HP tuning)"""
        pass

    def _train(self, user_object):
        runtime = BasicNativeRuntime()
        runtime.execute(user_object)

    def _deploy(self, user_object):
        deployment = NativeDeployment(self.namespace, self.job_name, self.runs)
        deployment.execute()


# class HPTuning(base.TrainingDecoratorInterface):
#     """Multiple trainings running in parallel to perform hyperparameters search
    
#     Arguments:
#         namespace {string} -- (optional) here the training should be deployed
#         runs {integer} -- (optional) the number of parallel runs to launch
#     """

#     def __init__(self, namespace=None, runs=1):
#         super(HPTuning, self).__init__(namespace, runs)
    
#     def _validate(self, user_object):
#         #TODO verify hp and train (or have hp part of the decorator)
#         raise NotImplementedError()


