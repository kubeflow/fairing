from fairing.constants import constants

from .base import BasePreProcessor
from fairing.notebook import notebook_util


class FullNotebookPreProcessor(BasePreProcessor):
    # TODO: Allow configuration of errors / timeout options
    def __init__(self,
                 notebook_file=None,
                 input_files=None,
                 command=["jupyter", "nbconvert", "--stdout", "--to", "notebook", "--execute", "--allow-errors",
                          "--ExecutePreprocessor.timeout=-1"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):

        if notebook_file is None and notebook_util.is_in_notebook():
            notebook_file = notebook_util.get_notebook_name()

        input_files = input_files or []
        if notebook_file not in input_files:
            input_files.append(notebook_file)

        super().__init__(
            executable=notebook_file,
            input_files=input_files,
            command=command,
            output_map=output_map,
            path_prefix=path_prefix)

