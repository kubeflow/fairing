import os
import signal
import sys
import shutil
import types
from collections import namedtuple

import metaparticle_pkg.builder as builder
import metaparticle_pkg.option as option
from metaml.backend import get_backend
from metaml.docker import is_in_docker_container, write_dockerfile

# class Serve(object):

  # def __init__(self, backend, options, package, tensorboard):
  #   self.backend = backend
  #   self.serving_options = TrainOptions(**options)
  #   self.package = option.load(option.PackageOptions, package)
  #   self.image = "{repo}/{name}:latest".format(
  #     repo=self.package.repository,
  #     name=self.package.name
  #   )

  #   self.builder = builder.select(self.package.builder)
  #   self.backend = get_backend(backend)
  
  # def __call__(self, func):
  #   def wrapped():
  #     if is_in_docker_container():
  #       return self.serve(func)

  #     exec_file = sys.argv[0]
  #     slash_ix = exec_file.find('/')
  #     if slash_ix != -1:
  #       exec_file = exec_file[slash_ix:]

  #     write_dockerfile(self.package, exec_file)
  #     self.builder.build(self.image)

  #     if self.package.publish:
  #       self.builder.publish(self.image)

  #     # def signal_handler(signal, frame):
  #     #   self.backend.cancel(self.package.name)
  #     #   sys.exit(0)
  #     # signal.signal(signal.SIGINT, signal_handler)

  #     # TODO: pass args
  #     self.backend.run(self.image, self.package.name, self.train_options, self.tensorboard_options)

  #     return self.backend.logs(self.package.name)
  #   return wrapped



