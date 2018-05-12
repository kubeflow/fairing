import types

class TrainingStrategy(object):
  def __init__(self):
    self.parallelism = 1

  def get_params(self):
    return {}

class DistributedTraining(TrainingStrategy):
  def __init__(self, ps_count, worker_count):
    super(DistributedTraining, self).__init__()
    self.ps_count = ps_count
    self.worker_count = worker_count
  
class HyperparameterTuning(TrainingStrategy):
  def __init__(self, hyper_parameters, parallelism=1, completion=None):
    super(HyperparameterTuning, self).__init__()
    self.hyper_parameters = hyper_parameters
    self.parallelism = parallelism
    self.completion = completion if completion else parallelism
  
  def get_params(self):
    if isinstance(self.hyper_parameters, types.FunctionType):
      return self.hyper_parameters()
    return self.hyper_parameters