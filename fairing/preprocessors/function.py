import cloudpickle
import fairing
import glob
import os
import types
import tempfile
from pathlib import Path
from enum import Enum

from fairing.constants import constants
from .base import BasePreProcessor
from fairing.functions.function_shim import get_execution_obj_type, ObjectType

FUNCTION_SHIM = 'function_shim.py'
SERIALIZED_FN_FILE = 'pickled_fn.p'

# TODO(@karthikv2k): Ref #122 Find a better way to support deployer specific preprocessing
OUTPUT_FILE = """import cloudpickle
{OBJ_NAME} = cloudpickle.load(open("{SERIALIZED_FN_FILE}", "rb"))
"""

class FunctionPreProcessor(BasePreProcessor):
    """
    FunctionPreProcessor preprocesses a single function.
    It sets as the command a function_shim that calls the function directly.

    args: function_name - the name of the function to be called
    """
    def __init__(self,
                 function_obj,
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None,
                 input_files=[]):
        super().__init__(
            output_map=output_map,
            path_prefix=path_prefix,
            input_files=input_files)

        if get_execution_obj_type(function_obj) ==  ObjectType.NOT_SUPPORTED:
            raise RuntimeError("Object must of type function or a class")
        
        fairing_dir = os.path.dirname(fairing.__file__)
        self.output_map[os.path.join(fairing_dir, "functions", FUNCTION_SHIM)] = \
            os.path.join(path_prefix, FUNCTION_SHIM)

        # Make sure the user code can be imported as a module
        self.output_map[os.path.join(fairing_dir, '__init__.py')] = \
            os.path.join(path_prefix, '__init__.py')

        # Make sure fairing can use imported as a module
        self.output_map[os.path.join(fairing_dir, '__init__.py')] = \
            os.path.join(path_prefix, "fairing", '__init__.py')

        # Make sure cloudpickle can be imported as a module 
        cloudpickle_dir = os.path.dirname(cloudpickle.__file__)
        self.output_map[os.path.join(cloudpickle_dir, '__init__.py')] = \
            os.path.join(path_prefix, "cloudpickle", '__init__.py')
        self.output_map[os.path.join(cloudpickle_dir, 'cloudpickle.py')] = \
            os.path.join(path_prefix, "cloudpickle", 'cloudpickle.py')
        
        _, temp_payload_file = tempfile.mkstemp()
        with open(temp_payload_file, "wb") as f:
            cloudpickle.dump(function_obj, f)
        # Adding the serialized file to the context
        payload_file_in_context = os.path.join(path_prefix, SERIALIZED_FN_FILE)
        self.output_map[temp_payload_file] = payload_file_in_context

        # TODO(@karthikv2k): Ref #122 Find a better way to support deployer specific preprocessing
        _, temp_payload_wrapper_file = tempfile.mkstemp()            
        with open(temp_payload_wrapper_file, "w") as f:
            contents  = OUTPUT_FILE.format(OBJ_NAME=function_obj.__name__, SERIALIZED_FN_FILE=SERIALIZED_FN_FILE)
            f.write(contents)
        # Adding the serialized file to the context
        payload_wrapper_file_in_context = os.path.join(path_prefix, function_obj.__name__ + ".py")
        self.output_map[temp_payload_wrapper_file] = payload_wrapper_file_in_context

        self.command = ["python", os.path.join(self.path_prefix, FUNCTION_SHIM),
                        "--serialized_fn_file", payload_file_in_context]

    def get_command(self):
        return self.command
