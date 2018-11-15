


#TODO: Defines what should be public or private better
#TODO: i.e. if a user wants to write a PolyaxonTraining, what are the methods
#TODO: that will need to be overwritten? backend, deploy
class BaseTraining(TrainingDecorator):

    def __init__(self,
                 namespace=None,
                 #TODO: implement TensorBoard in a higher level class
                 #  tensorboard=None,
                 #TODO: this should be refactored
                 #  architecture=architectures.BasicArchitecture(),
                 #  strategy=strategies.BasicTrainingStrategy(),
                 #TODO implement this: class that inherit from that should pass
                 #TODO: down the backend. I.e: Metaparticle/K8s/Polyaxon-client

                 #TODO: define a backend interface
                 #TODO: is this needed? Can training classes instead directly
                 #TODO: instantiate their desired backend?
                 #backend=metaparticle
                 ):
        
        super(BaseTraining, self).__init__()

        if namespace is None:
            self.namespace = self._get_default_target_namespace()
        else:            
            self.namespace = namespace
        # self.strategy = strategy
        # self.architecture = architecture
        # self.tensorboard_options = options.TensorboardOptions(**tensorboard) if tensorboard else None
        #TODO do we still need backend?
        # self.backend = self.architecture.get_associated_backend()
        # self.strategy.set_architecture(self.architecture)

    #TODO: this method should probably be overriden by every training to ensure
    #TODO: that the user object is compatible with the kind of training.
    #TODO: i.e for a simple training the user_object could be a class or 
    #TODO: a function. But for PBT it needs to be a class with train()
    #TODO: build() and hp()
    def __start_training(self, user_object):
        raise NotImplementedError()

    def __deploy_training(self):

        deployment = BaseDeployment()

        #TODO: create context object to pass around volume/volumeMounts
        #TODO: currently builder needs envs and writes it in the dockerfile.
        #TODO: instead we should add them on the pods at runtime
        #TODO: or pass everything to a context (envs, image fqdn, volumes)
        #TODO: and only build the image and compile the ast at the end
        config.get_builder().execute()
        #TODO: env becomes useless
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

    #TODO: where should this be called?
    def _get_default_target_namespace(self):
        if not is_running_in_k8s():
            return 'default'
        return get_current_k8s_namespace()

    def add_training(self):
        #TODO: Call builder.get_full_image_name()
        #TODO: use context to find volume/volume_mounts
        full_image_name = get_image_full(repository, image_name, image_tag)
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

    
class BaseHPTuning(BaseTraining):
    def __init__(self, namespace=None, nb_runs=1):

    def __start_training(self, user_class):
        raise NotImplementedError()

    def __deploy_training(self):
        #TODO: call add_training from baseTraining. It should return the specs
        #TODO: for a single training, and we can iterate on it
        raise NotImplementedError
    
    #TODO: ensure that it's a class with train() and hp() or do not
    #TODO: override validate and instead ask the user to provide distribution
    #TODO: in the decorator directly
    def __validate(self, user_object):
        raise NotImplementedError()
        