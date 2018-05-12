import types

class BasicTrainingStrategy(object):
  def __init__(self):
    self.runs = 1

  def get_params(self):
    return {}

class HyperparameterTuning(BasicTrainingStrategy):
  def __init__(self, hyper_parameters, runs=1):
    super(HyperparameterTuning, self).__init__()
    self.hyper_parameters = hyper_parameters
    self.runs = runs
  
  def get_params(self):
    if isinstance(self.hyper_parameters, types.FunctionType):
      return self.hyper_parameters()
    return self.hyper_parameters