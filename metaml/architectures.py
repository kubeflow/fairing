

class BasicArchitecture(): pass

class DistributedTraining(BasicArchitecture):
  def __init__(self, ps_count, worker_count):
    self.ps_count = ps_count
    self.worker_count = worker_count