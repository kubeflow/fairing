import signal
import sys
import types
from collections import namedtuple

import metaparticle_pkg.builder as builder
import metaparticle_pkg.option as option
from metaml.backend import get_backend
from metaml.docker import is_in_docker_container, write_dockerfile

class Train(object):
  # Calls the user defined training function 
  # and feed it with predifined, or user generated HP generator
  # containerize the code and deploy on k8s

  def __init__(self, backend, options, package, tensorboard):
    self.backend = backend
    self.train_options = TrainOptions(**options)
    self.tensorboard_options = TensorboardOptions(**tensorboard)
    self.package = option.load(option.PackageOptions, package)
    self.image = "{repo}/{name}:latest".format(
          repo=self.package.repository,
          name=self.package.name
      )

    self.builder = builder.select(self.package.builder)
    self.backend = get_backend(backend)
  
  def __call__(self, func):
    def wrapped():
      if is_in_docker_container():
        return self.exec_user_code(func)

      exec_file = sys.argv[0]
      slash_ix = exec_file.find('/')
      if slash_ix != -1:
        exec_file = exec_file[slash_ix:]

      write_dockerfile(self.package, exec_file)
      self.builder.build(self.image)

      if self.package.publish:
        self.builder.publish(self.image)

      def signal_handler(signal, frame):
        self.backend.cancel(self.package.name)
        sys.exit(0)
      signal.signal(signal.SIGINT, signal_handler)

      # TODO: pass args
      self.backend.run(self.image, self.package.name, self.train_options, self.tensorboard_options)

      return self.backend.logs(self.package.name)
    return wrapped

  def exec_user_code(self, func):
      params = None
      if isinstance(self.train_options.hyper_parameters, types.FunctionType):
        params = self.train_options.hyper_parameters()
      else:
        params = self.train_options.hyper_parameters

      return func(**params)


class TrainOptions(namedtuple('Train', 'hyper_parameters, parallelism, completion')):
  def __new__(cls, hyper_parameters={}, parallelism=1, completion=None):
    return super(TrainOptions, cls).__new__(cls, hyper_parameters, parallelism, completion)

# Todo: we should probably ask for the storageclass instead of the pvc_name and create a pvc on deployment.
# This would need to be implemented in the AST
class TensorboardOptions(namedtuple('Tensorboard', 'log_dir, pvc_name, public')):
  def __new__(cls, log_dir, pvc_name, public):
    return super(TensorboardOptions, cls).__new__(cls, log_dir, pvc_name, public)


