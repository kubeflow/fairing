import os

from kubeflow.fairing.preprocessors.base import BasePreProcessor
from kubeflow.fairing.constants import constants
from kubeflow.fairing.notebook import notebook_util


class FullNotebookPreProcessor(BasePreProcessor):
    """ The Full notebook preprocess for the context which comes from BasePreProcessor.
    :param BasePreProcessor: a context that gets sent to the builder for the docker build and
    sets the entrypoint
    """
    # TODO: Allow configuration of errors / timeout options
    def __init__(self,
                 notebook_file=None,
                 output_file="fairing_output_notebook.ipynb",
                 input_files=None,
                 command=None,
                 path_prefix=constants.DEFAULT_DEST_PREFIX,
                 output_map=None):
        """ Init the full notebook preprocess.
        :param notebook_file: the jupyter notebook file.
        :param output_file: the output file, the defaut name is 'fairing_output_notebook.ipynb'.
        :param input_files: the source files to be processed.
        :param command: the command to pass to the builder.
        :param path_prefix: the defaut destion path prefix '/app/'.
        :param output_map: a dict of files to be added without preprocessing.

        """
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


    def set_default_executable(self):
        """Ingore the default executable setting for the full_notebook preprocessor.
        """
        pass
