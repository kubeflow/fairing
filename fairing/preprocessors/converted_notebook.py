import nbconvert
import re
import tempfile
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


class FilterIncludeCell(NbPreProcessor):
    """Notebook preprocessor that only includes cells that have a comment fairing:include-cell"""
    _pattern = re.compile('.*fairing:include-cell.*')

    def filter_include_cell(self, src):
        filtered = []
        for line in src.splitlines():
            match = self._pattern.match(line)
            if match:
                return src
        return ''

    def preprocess_cell(self, cell, resources, index):
        if cell['cell_type'] == 'code':
            cell['source'] = self.filter_include_cell(cell['source'])

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
        self.not_overwrite = False

    def preprocess(self):
        if self.not_overwrite:
            return [self.executable]
        self.not_overwrite = True
        exporter = nbconvert.PythonExporter()
        exporter.register_preprocessor(self.notebook_preprocessor, enabled=True)
        contents, _ = exporter.from_filename(self.notebook_file)
        converted_notebook = Path(self.notebook_file).with_suffix('.py')
        if converted_notebook.exists():
            dir_name = Path(self.notebook_file).absolute().parent
            _, file_name = tempfile.mkstemp(suffix=".py", dir=dir_name)
            converted_notebook = Path(file_name[file_name.rfind('/')+1:])
        with open(converted_notebook, 'w') as f:
            f.write(contents)
        self.executable = converted_notebook
        return [converted_notebook]


class ConvertNotebookPreprocessorWithFire(ConvertNotebookPreprocessor):
    """Create an entrpoint using pyfire."""
    def __init__(self,
                 class_name=None,
                 notebook_file=None,
                 notebook_preprocessor=FilterIncludeCell,
                 executable=None,
                 command=["python"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):

        super().__init__(
            notebook_file=notebook_file,
            notebook_preprocessor=notebook_preprocessor,
            executable=executable,
            command=command,
            path_prefix=path_prefix,
            output_map=output_map)

        self.class_name = class_name
        self.not_overwrite = False

    def preprocess(self):
        if self.not_overwrite:
            results = [self.executable]
            results.extend(self.input_files)
            return results
        self.not_overwrite = True
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
        if converted_notebook.exists():
            dir_name = Path(self.notebook_file).absolute().parent
            _, file_name = tempfile.mkstemp(suffix=".py", dir=dir_name)
            converted_notebook = Path(file_name[file_name.rfind('/')+1:])
        with open(converted_notebook, 'w') as f:
            f.write(contents)
            f.write("\n")
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
