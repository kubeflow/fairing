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
    """Get the execution object type, the object can be a function or class.

    :param obj: The name of object such as the function or class
    :returns: int: The corresponding object type.

    """
    # Check if a function is provided
    if (isinstance(obj, types.FunctionType) or  #pylint:disable=consider-merging-isinstance
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


def compare_version(local_python_version):
    """Compare the Python major and minor version for local and remote python.

    :param local_python_version: Python version of local environment
    :returns: None.

    """
    remote_python_version = ".".join([str(x) for x in sys.version_info[0:2]])
    if local_python_version != remote_python_version:
        raise RuntimeError('The Python version ' + remote_python_version + ' mismatches \
                           with Python ' + local_python_version + ' in the local environment.')


def call(serialized_fn_file):
    """Get the content from serialized function.

    :param serialized_fn_file: the file includes serialized function
    :returns: object: The content of object.

    """
    with open(serialized_fn_file, 'rb') as f:
        obj = cloudpickle.load(f)
        obj_type = get_execution_obj_type(obj)
        if obj_type == ObjectType.FUNCTION:
            res = obj()
        elif obj_type == ObjectType.CLASS:
            res = obj().train()
        else:
            raise RuntimeError("Object must of type function or a \
                               class but got {}".format(type(obj)))
        if res:
            print(res)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Shim for calling a serialized function')
    parser.add_argument('--serialized_fn_file', action="store")
    parser.add_argument('--python_version', action="store")
    args = parser.parse_args()
    compare_version(args.python_version)
    call(args.serialized_fn_file)
