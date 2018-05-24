class BasicTrainingStrategy(object):
  def __init__(self):
    self.runs = 1
    self.arch = None
    self.backend = None

  def add_training(self, svc, img, name, volumes, volume_mounts):
   return self.arch.add_jobs(svc, self.runs, img, name, volumes, volume_mounts), None

  def get_params(self):
    return {}
  
  def exec_user_code(self, user_object):

    if 'build' in dir(user_object) and callable(getattr(user_object, 'build')):
      user_object.build()
    user_object.train()
  
  def set_architecture(self, arch):
    self.arch = arch
    self.backend = arch.get_associated_backend()

