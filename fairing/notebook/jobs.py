import fairing
from fairing.functions.function_shim import get_execution_obj_type, ObjectType
from fairing.preprocessors.function import FunctionPreProcessor
from fairing.builders.docker.docker import DockerBuilder
from fairing.deployers.job.job import Job
from fairing.deployers.serving.serving import Serving

def guess_preprocessor(obj, *args, **kwargs):
    if get_execution_obj_type(obj) != ObjectType.NOT_SUPPORTED:
        return FunctionPreProcessor(obj, *args, **kwargs) 
    else:
        raise NotImplementedError("obj param should be a function or a class, got {}".format(type(obj)))

def guess_docker_registry():
    try:
        gcp_project = fairing.cloud.gcp.guess_project_name()
        registry = 'gcr.io/{}'.format(gcp_project)
        return registry
    except Exception as e:
        return None

class BaseJob:
    
    def __init__(self, obj, base_docker_image, docker_registry=None, input_files=[]):
        if not docker_registry:
            guessed_docker_registry = guess_docker_registry()
            if not guessed_docker_registry:
                raise RuntimeError("Not able to guess docker registry, please specify docker_registry explicitly.")
            self.docker_registry = guessed_docker_registry
        else:
            self.docker_registry = docker_registry
        preprocessor = guess_preprocessor(obj, input_files=input_files)
        self.builder = DockerBuilder(preprocessor=preprocessor,
                                     base_image=base_docker_image,
                                     registry=self.docker_registry)
        
    def _build(self):
        self.builder.build()
        self.pod_spec = self.builder.generate_pod_spec()
    
class TrainJob(BaseJob):

    def __init__(self, obj, base_docker_image, docker_registry=None, input_files=[]):
        super().__init__(obj, base_docker_image, docker_registry, input_files)
        
    def submit(self):
        self._build()
        deployer = Job()
        deployer.deploy(self.pod_spec)

class PredictionEndpoint(BaseJob):
    
    def __init__(self, model_class, base_docker_image, docker_registry=None, input_files=[]):
        self.model_class = model_class
        super().__init__(model_class, base_docker_image, docker_registry, input_files)
    
    def create(self):
        self._build()
        deployer = Serving(serving_class=self.model_class.__name__)
        deployer.deploy(self.pod_spec)
        # TODO shoudl return a prediction endpoint client
