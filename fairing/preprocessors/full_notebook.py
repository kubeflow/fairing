import nbconvert
from nbconvert.preprocessors import Preprocessor as NbPreProcessor
from fairing.constants import constants

from .base import BasePreProcessor


class FullNotebookPreProcessor(BasePreProcessor):
    def __init__(self,
                 notebook_file=None,
                 command="ipython",
                 executable=None,
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):

        super().__init__(
            executable=executable,
            input_files=[notebook_file],
            command=command,
            output_map=output_map,
            path_prefix=path_prefix)