import os
from fairing.constants import constants

from .base import BasePreProcessor
from fairing.notebook import notebook_util


class FullNotebookPreProcessor(BasePreProcessor):
    # TODO: Allow configuration of errors / timeout options
    def __init__(self,
                 notebook_file=None,
                 output_file="fairing_output_notebook.ipynb",
                 input_files=None,
                 command=None,
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):

        if notebook_file is None and notebook_util.is_in_notebook():
            notebook_file = notebook_util.get_notebook_name()

        if notebook_file is None:
            raise ValueError('A notebook_file must be provided.')

        relative_notebook_file = notebook_file
        # Convert absolute notebook path to relative path
        if os.path.isabs(notebook_file[0]):
            relative_notebook_file = os.path.relpath(notebook_file)

        if command is None:
            command = ["papermill", relative_notebook_file, output_file, "--log-output"]

        input_files = input_files or []
        if relative_notebook_file not in input_files:
            input_files.append(relative_notebook_file)

        super().__init__(
            executable=None,
            input_files=input_files,
            command=command,
            output_map=output_map,
            path_prefix=path_prefix)


    # We don't want to set a default executable for the full_notebook preprocessor.
    def set_default_executable(self):
        pass

