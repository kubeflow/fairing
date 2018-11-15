import signal
import abc
import logging
import sys

import six

from fairing import config
from fairing import metaparticle
from fairing import options
from fairing import strategies
from fairing import architectures

logger = logging.getLogger(__name__)

@six.add_metaclass(abc.ABCMeta)
class DeploymentInterface(object):

    def execute(self):
        pass
    
    def validate(self, user_object):
        pass

@six.add_metaclass(abc.ABCMeta)
class RuntimeInterface(object):

    def execute(user_object):
        pass



@six.add_metaclass(abc.ABCMeta)
class TrainingDecoratorInterface(object):

    def __call__(self, cls):
        class UserClass(cls):
            # self refers to the BaseTraining instance
            # user_class is equivalent to self in the UserClass instance
            def __init__(user_class):
                user_class.is_training_initialized = False

            def __getattribute__(user_class, attribute_name):
                # Overriding train in order to minimize the changes 
                # necessary in the user code to go from local to remoten't be here probably
                # execution.
                # That way, by simply commenting or uncommenting the 
                # Train decorator model.train() will execute either on the local 
                # setup or in kubernetes.

                if (attribute_name != 'train'
                        or user_class.is_training_initialized):
                    return super(UserClass, user_class).__getattribute__(
                        attribute_name)

                if attribute_name == 'train' and not is_runtime_phase():
                    return super(UserClass, user_class).__getattribute__(
                        '_deploy_training')

                user_class.is_training_initialized = True
                self.__train(user_class)
                return super(UserClass, user_class).__getattribute__(
                    '_noop_attribute')

            def _noop_attribute(user_class):
                pass

            def _deploy_training(user_class):
                self._validate(user_class)
                self.__deploy(user_class)

        return UserClass

    @abc.abstractmethod
    def __validate(self, user_class):
        pass

    @abc.abstractmethod
    def __train(self, user_class):
        pass

    @abc.abstractmethod
    def __deploy(self, user_class):
        pass
