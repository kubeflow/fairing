from metaparticle_pkg import Containerize
import uuid

class Train(object):
  # Calls the user defined training function 
  # and feed it with predifined, or user generated HP generator
  # containerize the code and deploy on k8s using sharding (one shard per draw)

  def __init__(self, hp, draws):
    self.hp = hp
    self.draws = draws
    package = {'repository': 'wbuchwalter', 'name': 'trainer_{}'.format(uuid.uuid4())}
    runtime = {'replicas': draws}
    self.containerize = Containerize(package=package, runtime=runtime)
  
  def __call__(self, func):
    def wrapper():
      self.containerize(lambda: func(*self.hp))()
    return wrapper

def serve_prediction():
  return NotImplementedError
