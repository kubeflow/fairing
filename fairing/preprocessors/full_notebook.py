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

        if command is None:
            command = ["papermill", notebook_file, output_file, "--log-output"]
            executable = None
        else:
            executable = notebook_file

        input_files = input_files or []
        if notebook_file not in input_files:
            input_files.append(notebook_file)

        super().__init__(
            executable=executable,
            input_files=input_files,
            command=command,
            output_map=output_map,
            path_prefix=path_prefix)

