import types
from metaml.strategies.basic import BasicTrainingStrategy

class HyperparameterTuning(BasicTrainingStrategy):
  def __init__(self, hyperparameters, runs=1):
    super(HyperparameterTuning, self).__init__()
    self.hyperparameters = hyperparameters
    self.runs = runs
  
  def get_params(self):
    if isinstance(self.hyperparameters, types.FunctionType):
      return self.hyperparameters()
    return self.hyperparameters
  
  def exec_user_func(self, user_func):
    return user_func(**self.get_params())