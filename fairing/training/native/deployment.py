from fairing.training import base
from fairing import config
from fairing import utils

class NativeDeployment(base.DeploymentInterface):
    """Handle all the template building for metaparticle api and calling mpclient

    Attributes:
        namespace: K8s namespace where the training's components 
            will be deployed.
        runs: Number of training(s) to be deployed. Hyperparameter search
            will generate multiple jobs.
    """

    def __init__(self, namespace, runs):
        if namespace is None:
            self.namespace = 'fairing'
        else:
            self.namespace = namespace
        
        self.runs = runs
        self.builder = config.get_builder()

    def execute(self):
        #TODO: create context object to pass around volume/volumeMounts
        #TODO: currently builder needs envs and writes it in the dockerfile.
        #TODO: instead we should add them on the pods at runtime
        #TODO: or pass everything to a context (envs, image fqdn, volumes)
        #TODO: and only build the image and compile the ast at the end
        self.builder.execute()
        ast, env = self._compile_ast()

        mp_client = metaparticle.MetaparticleClient()
        
        def signal_handler(signal, frame):
            mp_client.cancel(self.image_name)
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        mp_client.run(ast)

        logger.warn("Training(s) launched.")

        if stream_logs:
            self.backend.stream_logs(self.image_name, self.image_tag)

    def _compile_ast(self):
        ast = self.get_base_ast()
        volumes = None
        volume_mounts = None
        # if self.tensorboard_options:
        #     ast, volumes, volume_mounts = self.backend.add_tensorboard(
        #         ast, self.image_name, self.tensorboard_options)
        
        ast, env = self.add_training(
            ast, self.repository, self.image_name, self.image_tag, volumes, volume_mounts)
        return ast, env

    def _get_default_target_namespace(self):
        if not utils.is_running_in_k8s():
            return 'default'
        return utils.get_current_k8s_namespace()

    def add_training(self):
        #TODO: Call builder.get_full_image_name()
        #TODO: use context to find volume/volume_mounts
        full_image_name = utils.get_image_full_name(repository, image_name, image_tag)
        svc['jobs'] = [{
            "name": image_name,
            # TODO should parallelism and completion be surfaced ? How would that be implemented in all backends
            "parallelism": count,
            "completion": count,
            "containers": [
                {
                    "image": full_image_name,
                    "volumeMounts": volume_mounts
                }
            ],
            "volumes": volumes
        }]
        return svc
    
    def get_base_ast(self):
        return {
            "namespace": self.namespace,
            "name": "{name}-{tag}".format(name=self.image_name, tag=self.image_tag),
            # Metaparticle does not generate a default GUID,
            # and we don't care about it's actual value
            "guid": 123456
        }        