import logging
import nbconvert
import re
from nbconvert.preprocessors import Preprocessor as NbPreProcessor
from pathlib import Path

from .base import BasePreProcessor
from ..notebook import notebook_util
from ..constants import constants


class FilterMagicCommands(NbPreProcessor):
    _magic_pattern = re.compile('^!|^%')

    def filter_magic_commands(self, src):
        filtered = []
        for line in src.splitlines():
            match = self._magic_pattern.match(line)
            if match is None:
                filtered.append(line)
        return '\n'.join(filtered)

    def preprocess_cell(self, cell, resources, index): #pylint:disable=unused-argument
        if cell['cell_type'] == 'code':
            cell['source'] = self.filter_magic_commands(cell['source'])
        return cell, resources


class FilterIncludeCell(NbPreProcessor):
    """Notebook preprocessor that only includes cells that have a comment fairing:include-cell"""
    _pattern = re.compile('.*fairing:include-cell.*')

    def filter_include_cell(self, src):
        for line in src.splitlines():
            match = self._pattern.match(line)
            if match:
                return src
        return ''

    def preprocess_cell(self, cell, resources, index): #pylint:disable=unused-argument
        if cell['cell_type'] == 'code':
            cell['source'] = self.filter_include_cell(cell['source'])

        return cell, resources


class ConvertNotebookPreprocessor(BasePreProcessor):
    def __init__(self, #pylint:disable=dangerous-default-value
                 notebook_file=None,
                 notebook_preprocessor=FilterMagicCommands,
                 executable=None,
                 command=["python"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None,
                 overwrite=True):

        super().__init__(
            executable=executable,
            input_files=[],
            output_map=output_map,
            path_prefix=path_prefix)

        if notebook_file is None and notebook_util.is_in_notebook():
            notebook_file = notebook_util.get_notebook_name()

        self.notebook_file = notebook_file
        self.notebook_preprocessor = notebook_preprocessor
        self.overwrite = overwrite

    def preprocess(self):
        exporter = nbconvert.PythonExporter()
        exporter.register_preprocessor(self.notebook_preprocessor, enabled=True)
        contents, _ = exporter.from_filename(self.notebook_file)
        converted_notebook = Path(self.notebook_file).with_suffix('.py')
        if converted_notebook.exists() and not self.overwrite:
            raise Exception('Default path {} exists but overwrite flag\
                            is False'.format(converted_notebook))
        with open(converted_notebook, 'w') as f:
            logging.info('Converting {} to {}'.format(self.notebook_file, converted_notebook))
            f.write(contents)
        self.executable = converted_notebook
        return [converted_notebook]


class ConvertNotebookPreprocessorWithFire(ConvertNotebookPreprocessor):
    """Create an entrpoint using pyfire."""
    def __init__(self, #pylint:disable=dangerous-default-value
                 class_name=None,
                 notebook_file=None,
                 notebook_preprocessor=FilterIncludeCell,
                 executable=None,
                 command=["python"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None,
                 overwrite=True):

        super().__init__(
            notebook_file=notebook_file,
            notebook_preprocessor=notebook_preprocessor,
            executable=executable,
            command=command,
            path_prefix=path_prefix,
            output_map=output_map)

        self.class_name = class_name
        self.overwrite = overwrite

    def preprocess(self):
        exporter = nbconvert.PythonExporter()
        exporter.register_preprocessor(self.notebook_preprocessor, enabled=True)
        processed, _ = exporter.from_filename(self.notebook_file)

        lines = []
        for l in processed.splitlines():
            # Get rid of multiple blank lines
            if not l.strip():
                if lines:
                    if not lines[-1]:
                        # last line is already blank don't add another one
                        continue
            # strip in statements
            if l.startswith("# In["):
                continue
            lines.append(l)

        contents = "\n".join(lines)
        converted_notebook = Path(self.notebook_file).with_suffix('.py')
        if converted_notebook.exists() and not self.overwrite:
            raise Exception('Default path {} exists but overwrite flag\
                            is False'.format(converted_notebook))
        with open(converted_notebook, 'w') as f:
            logging.info('Converting {} to {}'.format(self.notebook_file, converted_notebook))
            f.write(contents)
            f.write("\n")
            logging.info('Creating entry point for the class name {}'.format(self.class_name))
            f.write("""
if __name__ == "__main__":
  import fire
  import logging
  logging.basicConfig(format='%(message)s')
  logging.getLogger().setLevel(logging.INFO)
  fire.Fire({0})
""".format(self.class_name))
        self.executable = converted_notebook
        results = [converted_notebook]
        results.extend(self.input_files)
        return results
