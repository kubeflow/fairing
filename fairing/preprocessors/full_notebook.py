from fairing.constants import constants

from .base import BasePreProcessor
from fairing.notebook import notebook_util


class FullNotebookPreProcessor(BasePreProcessor):
    def __init__(self,
                 notebook_file=None,
                 command=["jupyter", "nbconvert", "--stdout", "--to", "notebook", "--execute"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):
        
        if notebook_file is None and notebook_util.is_in_notebook():
            notebook_file = notebook_util.get_notebook_name()
        
        super().__init__(
            executable=notebook_file,
            input_files=[notebook_file],
            command=command,
            output_map=output_map,
            path_prefix=path_prefix)

