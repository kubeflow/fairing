import logging
import nbconvert
import re
from nbconvert.preprocessors import Preprocessor as NbPreProcessor
from pathlib import Path

from kubeflow.fairing.preprocessors.base import BasePreProcessor
from kubeflow.fairing.notebook import notebook_util
from kubeflow.fairing.constants import constants


class FilterMagicCommands(NbPreProcessor):
    """Notebook preprocessor that have a comment which started with '!' or '%'.
    :param NbPreProcessor: the notebook preprocessor.
    """
    _magic_pattern = re.compile('^!|^%')

    def filter_magic_commands(self, src):
        """Filter out the source commands with magic pattern.

        :param src: the source commands.
        :returns: filtered: the filtered commands list.

        """
        filtered = []
        for line in src.splitlines():
            match = self._magic_pattern.match(line)
            if match is None:
                filtered.append(line)
        return '\n'.join(filtered)

    def preprocess_cell(self, cell, resources, index): #pylint:disable=unused-argument
        """preprocessor that includes cells

        :param: cell: the notebook cell.
        :param: resources: the code source of the notebook cell.
        :param: index: unused argumnet.
        :return: cell,resources: the notebook cell and its filtered with magic pattern commands.

        """
        if cell['cell_type'] == 'code':
            cell['source'] = self.filter_magic_commands(cell['source'])
        return cell, resources


class FilterIncludeCell(NbPreProcessor):
    """Notebook preprocessor that only includes cells that have a comment 'fairing:include-cell'.
    :param NbPreProcessor: the notebook preprocessor.
    """
    _pattern = re.compile('.*fairing:include-cell.*')

    def filter_include_cell(self, src):
        """Filter the cell that have a comment 'fairing:include-cell'.

        :param: src: the source cell.
        :returns: src: if the source cell matched the filter pattern, or Null.

        """
        for line in src.splitlines():
            match = self._pattern.match(line)
            if match:
                return src
        return ''

    def preprocess_cell(self, cell, resources, index): #pylint:disable=unused-argument
        """ Preprocess the notebook cell.

        :param cell: the notebook cell
        :param resources: the code source of the notebook cell.
        :param index: unused argumnet.
        :return: cell,resources: the notebook cell and its filtered with magic pattern commands.

        """
        if cell['cell_type'] == 'code':
            cell['source'] = self.filter_include_cell(cell['source'])

        return cell, resources


class ConvertNotebookPreprocessor(BasePreProcessor):
    """Convert the notebook preprocessor.
    :param BasePreProcessor: a context that gets sent to the builder for the docker build
    and sets the entrypoint.
    """
    def __init__(self, #pylint:disable=dangerous-default-value
                 notebook_file=None,
                 notebook_preprocessor=FilterMagicCommands,
                 executable=None,
                 command=["python"],
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None,
                 overwrite=True):
        """The init function ConvertNotebookPreprocessor class.
        :param notebook_file: the notebook file.
        :param notebook_preprocessor: the class FilterMagicCommands.
        :param executable: the file to execute using command (e.g. main.py)
        :param command: the python command.
        :param path_prefix: the defaut destion path prefix '/app/'.
        :param output_map: a dict of files to be added without preprocessing.
        """

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
        """Preprocessor the Notebook
        :return:[]: the converted notebook list.
        """
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
        """The init function ConvertNotebookPreprocessorWithFire class
        :param class_name: the name of the notebook preprocessor.
        :param notebook_file: the notebook file.
        :param notebook_preprocessor: the class FilterIncludeCell.
        :param command: the python command.
        :param path_prefix: the defaut destion path prefix '/app/'.
        :param output_map: a dict of files to be added without preprocessing.
        """

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
        """Preprocessor the Notebook.
        :return: results: the preprocessed notebook list.
        """
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
