class BasicTrainingStrategy(object):
  def __init__(self):
    self.runs = 1
    self.arch = None
    self.backend = None

  def add_training(self, svc, img, name, volumes, volume_mounts):
   return self.arch.add_jobs(svc, self.runs, img, name, volumes, volume_mounts), None

  def get_params(self):
    return {}
  
  def exec_user_func(self, user_func):
    user_func()
  
  def set_architecture(self, arch):
    self.arch = arch
    self.backend = arch.get_associated_backend()

