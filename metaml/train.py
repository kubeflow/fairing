import signal
import sys
import types
import logging
import shutil

from metaml.backend import get_backend, Native
from metaml.docker import is_in_docker_container, DockerBuilder
from metaml.options import TensorboardOptions, PackageOptions
from metaml.strategies import BasicTrainingStrategy
from metaml.architectures import BasicArchitecture

logger = logging.getLogger('metaml')

class Train(object):
  # Calls the user defined training function 
  # and feed it with predifined, or user generated HP generator
  # containerize the code and deploy on k8s

  def __init__(self, package, tensorboard=None, backend=Native, architecture=BasicArchitecture(), strategy=BasicTrainingStrategy()):
    self.backend = backend
    # self.train_options = TrainOptions(**options)
    self.strategy = strategy
    self.architecture = architecture
    self.tensorboard_options = TensorboardOptions(**tensorboard) if tensorboard else None
    self.package = PackageOptions(**package)
    self.image = "{repo}/{name}:latest".format(
          repo=self.package.repository,
          name=self.package.name
      )

    self.builder = DockerBuilder()
    self.backend = get_backend(backend)
    self.backend.init_training(self.architecture, self.strategy, self.tensorboard_options)
  
  def __call__(self, func):
    def wrapped():
      if is_in_docker_container():
        return self.exec_user_code(func)

      exec_file = sys.argv[0]
      slash_ix = exec_file.find('/')
      if slash_ix != -1:
        exec_file = exec_file[slash_ix:]

      self.builder.write_dockerfile(self.package, exec_file)
      self.builder.build(self.image)

      if self.package.publish:
        self.builder.publish(self.image)

      def signal_handler(signal, frame):
        self.backend.cancel(self.package.name)
        sys.exit(0)
      signal.signal(signal.SIGINT, signal_handler)

      # TODO: pass args
      self.backend.run_training(self.image, self.package.name)
      print("Training(s) launched.")

      return self.backend.logs(self.package.name)
    return wrapped

  def exec_user_code(self, func):
      return func(**self.strategy.get_params())



