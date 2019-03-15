import nbconvert
import re
from nbconvert.preprocessors import Preprocessor as NbPreProcessor
from fairing.constants import constants
from pathlib import Path

from .base import BasePreProcessor
from fairing.notebook import notebook_util


class FilterMagicCommands(NbPreProcessor):
    _magic_pattern = re.compile('^!|^%')

    def filter_magic_commands(self, src):
        filtered = []
        for line in src.splitlines():
            match = self._magic_pattern.match(line)
            if match is None:
                filtered.append(line)
        return '\n'.join(filtered)

    def preprocess_cell(self, cell, resources, index):
        if cell['cell_type'] == 'code':
            cell['source'] = self.filter_magic_commands(cell['source'])
        return cell, resources


class ConvertNotebookPreprocessor(BasePreProcessor):
    def __init__(self,
                 notebook_file=None,
                 notebook_preprocessor=FilterMagicCommands,
                 executable=None,
                 command=["python"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):

        super().__init__(
            executable=executable,
            input_files=[],
            output_map=output_map,
            path_prefix=path_prefix)

        if notebook_file is None and notebook_util.is_in_notebook():
            notebook_file = notebook_util.get_notebook_name()

        self.notebook_file = notebook_file
        self.notebook_preprocessor = notebook_preprocessor

    def preprocess(self):
        exporter = nbconvert.PythonExporter()
        exporter.register_preprocessor(self.notebook_preprocessor, enabled=True)
        contents, _ = exporter.from_filename(self.notebook_file)
        converted_notebook = Path(self.notebook_file).with_suffix('.py')
        with open(converted_notebook, 'w') as f:
            f.write(contents)
        self.executable = converted_notebook
        return [converted_notebook]
