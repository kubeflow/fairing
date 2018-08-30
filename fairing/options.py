from collections import namedtuple

from fairing.utils import get_unique_tag

# Todo: we should probably ask for the storageclass instead of the pvc_name and create a pvc on deployment.
# This would need to be supported in the AST
class TensorboardOptions(namedtuple('Tensorboard', 'log_dir, pvc_name, public')):
  def __new__(cls, log_dir, pvc_name, public):
    return super(TensorboardOptions, cls).__new__(cls, log_dir, pvc_name, public)

class PackageOptions(namedtuple('Package', 'repository name tag builder publish py_version dockerfile')):
    required_options = ['repository']

    def __new__(cls, repository, name=None, tag=None, builder='docker', publish=False, py_version=3, dockerfile=None):
        if not name:
            name = 'fairing-build'
            tag = get_unique_tag()
        else:
            tag = tag if tag else 'latest'
        return super(PackageOptions, cls).__new__(cls, repository, name, tag, builder, publish, py_version, dockerfile)