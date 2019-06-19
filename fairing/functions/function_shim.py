import argparse
import cloudpickle
import sys
import types
from enum import Enum
import logging

logging.basicConfig(format='%(message)s')
logging.getLogger().setLevel(logging.INFO)

class ObjectType(Enum):
    FUNCTION = 1
    CLASS = 2
    NOT_SUPPORTED = 3

def get_execution_obj_type(obj):
    # Check if a function is provided
    if (isinstance(obj, types.FunctionType) or
        isinstance(obj, types.BuiltinFunctionType) or
        isinstance(obj, types.BuiltinMethodType)):
        return ObjectType.FUNCTION

    # Reject class methods provided directly
    if isinstance(obj, types.MethodType):
        return ObjectType.NOT_SUPPORTED

    # Check if a class is provided (Python 3)
    if isinstance(obj, type) and hasattr(obj, 'train'):
        return ObjectType.CLASS

    return ObjectType.NOT_SUPPORTED

# compare the Python major and minor version for local and remote python
def compare_version(local_python_version):
    remote_python_version = ".".join([str(x) for x in sys.version_info[0:2]])
    if local_python_version != remote_python_version:
        logging.error("ERROR: The Python version mismatches with the local environment.")
        sys.exit(1)


def call(serialized_fn_file):
    with open(serialized_fn_file, 'rb') as f:
        obj = cloudpickle.load(f)
        obj_type = get_execution_obj_type(obj)
        if obj_type == ObjectType.FUNCTION:
            res = obj()
        elif obj_type == ObjectType.CLASS:
            res = obj().train()
        else:
            raise RuntimeError("Object must of type function or a class but got {}".format(type(obj)))
        if res:
            print(res)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Shim for calling a serialized function')
    parser.add_argument('--serialized_fn_file', action="store")
    parser.add_argument('--python_version', action="store")
    args = parser.parse_args()
    compare_version(args.python_version)
    call(args.serialized_fn_file)
