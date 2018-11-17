from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from future import standard_library
standard_library.install_aliases()

import types
from fairing.strategies.basic import BasicTrainingStrategy


class HyperparameterTuning(BasicTrainingStrategy):
    def __init__(self, runs=1):
        super(HyperparameterTuning, self).__init__()
        self.runs = runs

    # def get_params(self):
    #   if isinstance(self.hyperparameters, types.FunctionType):
    #     return self.hyperparameters()
    #   return self.hyperparameters

    def exec_user_code(self, user_object):
        hp = None

        # hyperparameters method is not mandatory
        hp_func = getattr(user_object, "hyperparameters", None)
        if callable(hp_func):
            hp = hp_func()
        user_object.build(hp)
        user_object.train(hp)
        # return user_func(**self.get_params())
