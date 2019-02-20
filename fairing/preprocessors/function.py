import fairing
import glob
import os
from pathlib import Path

from fairing.constants import constants
from .base import BasePreProcessor

FUNCTION_SHIM = 'function_shim.py'


class FunctionPreProcessor(BasePreProcessor):
    """
    FunctionPreProcessor preprocesses a single function.
    It sets as the command a function_shim that calls the function directly.

    args: function_name - the name of the function to be called
    """
    def __init__(self,
                 function_name,
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map={}):

        super().__init__(
            output_map=output_map,
            path_prefix=path_prefix)


        fairing_dir = os.path.dirname(fairing.__file__)
        self.output_map[os.path.join(fairing_dir, "functions", FUNCTION_SHIM)] = \
            os.path.join(path_prefix, FUNCTION_SHIM)

        # Make sure the user code can be imported as a module
        self.output_map[os.path.join(fairing_dir, '__init__.py')] = \
            os.path.join(path_prefix, '__init__.py')

        # Make sure fairing can use imported as a module
        self.output_map[os.path.join(fairing_dir, '__init__.py')] = \
            os.path.join(path_prefix, "fairing", '__init__.py')

        exec_module = str(Path(self.executable).with_suffix(''))

        self.command = ["python", os.path.join(self.path_prefix, FUNCTION_SHIM),
                        "--module_name", exec_module,
                        "--function_name", function_name]

    def get_command(self):
        return self.command