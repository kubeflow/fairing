import signal
import sys
import types
import logging
import shutil

# from fairing.backend import get_backend, Native
from fairing.builders import get_container_builder
from fairing.utils import is_runtime_phase, get_image_full
from fairing.options import TensorboardOptions
from fairing.architectures.native.basic import BasicArchitecture
from fairing.strategies.basic import BasicTrainingStrategy
from fairing.metaparticle import MetaparticleClient
from fairing.utils import get_unique_tag, is_running_in_k8s, get_current_k8s_namespace

logger = logging.getLogger('fairing')

class Trainer(object):
    def __init__(self,
                 repository,
                 image_name='fairing-job',
                 image_tag=None,
                 publish=True,
                 namespace=None,
                 dockerfile=None,
                 base_image=None,
                 tensorboard=None,
                 architecture=BasicArchitecture(),
                 strategy=BasicTrainingStrategy(),
                 builder=None):

        self.repository = repository
        self.image_name = image_name
        self.image_tag = image_tag

        # Target namespace where the job(s) will be deployed
        self.namespace = namespace or self.get_default_target_namespace()
        self.publish = publish
        self.base_image = base_image
        self.dockerfile = dockerfile

        self.strategy = strategy
        self.architecture = architecture
        self.tensorboard_options = TensorboardOptions(**tensorboard) if tensorboard else None
        self.backend = self.architecture.get_associated_backend()
        self.strategy.set_architecture(self.architecture)

        self.builder = get_container_builder(builder)

        self.full_image_name = None


    def get_default_target_namespace(self):
        if not is_running_in_k8s():
            return 'default'
        return get_current_k8s_namespace()

    def get_base_ast(self):
        return {
            "namespace": self.namespace,
            "name": "{name}-{tag}".format(name=self.image_name, tag=self.image_tag),
            # Metaparticle does not generate a default GUID,
            # and we don't care about it's actual value
            "guid": 123456
        }
    
    def compile_ast(self):
        ast = self.get_base_ast()
        volumes = None
        volume_mounts = None
        if self.tensorboard_options:
            ast, volumes, volume_mounts = self.backend.add_tensorboard(
                ast, self.image_name, self.tensorboard_options)
        
        ast, env = self.strategy.add_training(
            ast, self.repository, self.image_name, self.image_tag, volumes, volume_mounts)
        return ast, env

    def get_metaparticle_client(self):
        return MetaparticleClient()

    def fill_image_name_and_tag(self):
        if self.image_tag is None:
            self.image_tag = get_unique_tag()
        
        self.full_image_name = get_image_full(
            self.repository, self.image_name, self.image_tag)

    def deploy_training(self, stream_logs=True):
        self.fill_image_name_and_tag()
        ast, env = self.compile_ast()

        self.builder.execute(self.repository,
                             self.image_name,
                             self.image_tag,
                             self.base_image,
                             self.dockerfile,
                             self.publish,
                             env)

        mp = self.get_metaparticle_client()

        def signal_handler(signal, frame):
            mp.cancel(self.image_name)
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        mp.run(ast)

        logger.warn("Training(s) launched.")

        if stream_logs:
            self.backend.stream_logs(self.image_name, self.image_tag)

    def start_training(self, user_class):
        self.strategy.exec_user_code(user_class)


class Train(object):
    def __init__(self,
                 repository,
                 image_name='fairing-job',
                 image_tag=None,
                 publish=True,
                 namespace=None,
                 dockerfile=None,
                 base_image=None,
                 tensorboard=None,
                 architecture=BasicArchitecture(),
                 strategy=BasicTrainingStrategy(),
                 builder=None):

        self.trainer = Trainer(repository=repository,
                               image_name=image_name,
                               image_tag=image_tag,
                               publish=publish,
                               namespace=namespace,
                               dockerfile=dockerfile,
                               base_image=base_image,
                               tensorboard=tensorboard,
                               architecture=architecture,
                               strategy=strategy,
                               builder=builder)

    def __call__(self, cls):
        class UserClass(cls):
            # self refers to the Train instance
            # user_class is equivalentto self in the UserClass instance
            def __init__(user_class):
                user_class.is_training_initialized = False

            def __getattribute__(user_class, attribute_name):
                # Overriding train in order to minimize the changes necessary in the user
                # code to go from local to remote execution.
                # That way, by simply commenting or uncommenting the Train decorator
                # Model.train() will execute either on the local setup or in kubernetes

                if attribute_name != 'train' or user_class.is_training_initialized:
                    return super(UserClass, user_class).__getattribute__(attribute_name)

                if attribute_name == 'train' and not is_runtime_phase():
                    return super(UserClass, user_class).__getattribute__('_deploy_training')

                user_class.is_training_initialized = True
                self.trainer.start_training(user_class)
                return super(UserClass, user_class).__getattribute__('_noop_attribute')

            def _noop_attribute(user_class):
                pass

            def _deploy_training(user_class):
                self.trainer.deploy_training()

        return UserClass
