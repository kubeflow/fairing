from collections import namedtuple

class ServeOptions(namedtuple('Serve', 'route, port, replicas')):
  def __new__(cls, route='/predict', port=80, replicas=1):    
    return super(ServeOptions, cls).__new__(cls, route, port, replicas)

# class TrainOptions(namedtuple('Train', 'hyper_parameters, parallelism, completion, distributed_training')):
#   def __new__(cls, hyper_parameters={}, parallelism=1, completion=None, distributed_training=None):
#     if not completion:
#       completion = parallelism
#     distributed_training = DistributedTrainingOptions(**distributed_training)
#     return super(TrainOptions, cls).__new__(cls, hyper_parameters, parallelism, completion, distributed_training)

# class DistributedTrainingOptions(namedtuple('DistributedTraining', 'ps, worker')):
#   def __new__(cls, ps, worker):
#     return super(DistributedTrainingOptions, cls).__new__(cls, ps, worker)

# Todo: we should probably ask for the storageclass instead of the pvc_name and create a pvc on deployment.
# This would need to be supported in the AST
class TensorboardOptions(namedtuple('Tensorboard', 'log_dir, pvc_name, public')):
  def __new__(cls, log_dir, pvc_name, public):
    return super(TensorboardOptions, cls).__new__(cls, log_dir, pvc_name, public)

class PackageOptions(namedtuple('Package', 'repository name builder publish py_version')):
    required_options = ['repository']

    def __new__(cls, repository, name, builder='docker', publish=False, py_version=3, dockerfile=None):
        name = name if name else os.path.basename(os.getcwd())
        return super(PackageOptions, cls).__new__(cls, repository, name, builder, publish, py_version)
