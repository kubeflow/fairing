from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from future import standard_library
standard_library.install_aliases()
import signal
import abc
import logging
import sys

import six

from fairing import utils

logger = logging.getLogger(__name__)

@six.add_metaclass(abc.ABCMeta)
class TrainingDecoratorInterface(object):

    def __call__(self, cls):
        class UserClass(cls):
            # self refers to the BaseTraining instance
            # user_object is equivalent to self in the UserClass instance
            def __init__(user_object):
                user_object.is_training_initialized = False

            def __getattribute__(user_object, attribute_name):
                # Overriding train in order to minimize the changes 
                # necessary in the user code to go from local to remoten't be here probably
                # execution.
                # That way, by simply commenting or uncommenting the 
                # Train decorator model.train() will execute either on the local 
                # setup or in kubernetes.

                if (attribute_name != 'train'
                        or user_object.is_training_initialized):
                    return super(UserClass, user_object).__getattribute__(
                        attribute_name)

                if attribute_name == 'train' and not utils.is_runtime_phase():
                    return super(UserClass, user_object).__getattribute__(
                        '_deploy_training')

                user_object.is_training_initialized = True
                self._train(user_object)
                return super(UserClass, user_object).__getattribute__(
                    '_noop_attribute')

            def _noop_attribute(user_object):
                pass

            def _deploy_training(user_object):
                self._validate(user_object)
                self._deploy(user_object)

        return UserClass

    @abc.abstractmethod
    def _validate(self, user_object):
        pass

    @abc.abstractmethod
    def _train(self, user_object):
        pass

    @abc.abstractmethod
    def _deploy(self, user_object):
        pass
