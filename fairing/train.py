import signal
import sys
import types
import logging
import shutil

# from fairing.backend import get_backend, Native
from fairing.docker import is_in_docker_container, DockerBuilder
from fairing.options import TensorboardOptions, PackageOptions
from fairing.architectures.native.basic import BasicArchitecture
from fairing.strategies.basic import BasicTrainingStrategy
import fairing.metaparticle as mp

logger = logging.getLogger('fairing')

class Train(object):
    def __init__(self, package, tensorboard=None, architecture=BasicArchitecture(), strategy=BasicTrainingStrategy()):
        self.strategy = strategy
        self.architecture = architecture
        self.tensorboard_options = TensorboardOptions(
            **tensorboard) if tensorboard else None

        self.backend = self.architecture.get_associated_backend()
        self.strategy.set_architecture(self.architecture)

        if is_in_docker_container():
            return
        
        self.package = PackageOptions(**package)
        self.image = "{repo}/{name}:latest".format(
            repo=self.package.repository,
            name=self.package.name
        )
        self.builder = DockerBuilder()

        exec_file = sys.argv[0]
        slash_ix = exec_file.find('/')
        if slash_ix != -1:
            exec_file = exec_file[slash_ix:]

        ast, env = self.compile_ast()

        self.builder.write_dockerfile(self.package, exec_file, env)
        self.builder.build(self.image)

        if self.package.publish:
            self.builder.publish(self.image)

        def signal_handler(signal, frame):
            mp.cancel(self.package.name)
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)

        mp.run(ast)
        print("Training(s) launched.")

        mp.logs(self.package.name)
    
    def compile_ast(self):
        svc = {
            "name": self.package.name,
            "guid": 1234567
        }

        volumes = None
        volume_mounts = None
        if self.tensorboard_options:
            svc, volumes, volume_mounts = self.backend.add_tensorboard(
                svc, self.package.name, self.tensorboard_options)

        svc, env = self.strategy.add_training(
            svc, self.image, self.package.name, volumes, volume_mounts)
        return svc, env

    def __call__(self, cls):
        class UserClass(cls):
            def __call__(other):
                if is_in_docker_container():
                    self.strategy.exec_user_code(other)
                
        return UserClass
