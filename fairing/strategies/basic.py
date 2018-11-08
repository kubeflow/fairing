import logging

logger = logging.getLogger(__name__)


class BasicTrainingStrategy(object):

  def __init__(self):
    self.runs = 1
    self.arch = None
    self.backend = None

  def add_training(self, svc, repository, image_name, image_tag, volumes, volume_mounts):
   return self.arch.add_jobs(svc, self.runs, repository, image_name, image_tag, volumes, volume_mounts), None

  def get_params(self):
    return {}
  
  def exec_user_code(self, curr_class, user_class, attribute_name):
    logger.debug("curr_class %s user_class %s", curr_class, user_class)
    if 'build' in dir(user_class) and callable(getattr(user_class, 'build')):
      user_class.build()
    return super(curr_class, user_class).__getattribute__(attribute_name)
  
  def set_architecture(self, arch):
    self.arch = arch
    self.backend = arch.get_associated_backend()
