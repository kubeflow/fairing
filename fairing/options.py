from collections import namedtuple

# Todo: we should probably ask for the storageclass instead of the pvc_name and create a pvc on deployment.
# This would need to be supported in the AST
class TensorboardOptions(namedtuple('Tensorboard', 'log_dir, pvc_name, public')):
  def __new__(cls, log_dir, pvc_name, public):
    return super(TensorboardOptions, cls).__new__(cls, log_dir, pvc_name, public)