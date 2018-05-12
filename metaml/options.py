from collections import namedtuple

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
