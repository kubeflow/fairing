
from fairing.constants import constants
from fairing import utils

import os
import fairing
import tarfile
import glob

class BasePreProcessor(object):
    def __init__(
        self,
        input_files=glob.glob("**", recursive=True),
        command=["python"],
        executable=None,
        path_prefix=constants.DEFAULT_DEST_PREFIX,
        output_map={}
    ):
        self.executable = executable
        self.input_files = input_files
        self.output_map = output_map
        self.path_prefix = path_prefix
        self.command = command

        self.set_default_executable()
            
    def set_default_executable(self):
        if self.executable is not None:
            return
        if len(self.input_files) == 1:
            self.executable = self.input_files[0]
            return
        python_files = [item for item in self.input_files if item.endswith(".py")]
        if len(python_files) == 1:
            self.executable = python_files[0]
            return

    def preprocess(self):
        return self.input_files

    def context_map(self):
        c_map = self.fairing_runtime_files()
        for f in self.input_files:
            c_map[f] = os.path.join(self.path_prefix, f)

        for k, v in self.output_map.items():
            c_map[k] = v

        return c_map

    def context_tar_gz(self, output_file=constants.DEFAULT_CONTEXT_FILENAME):
        self.input_files = self.preprocess()
        with tarfile.open(output_file, "w:gz") as tar:
            for src, dst in self.context_map().items():
                tar.add(src, filter=reset_tar_mtime, arcname=dst)
        self._context_tar_path = output_file
        return output_file, utils.crc(self._context_tar_path)

    def get_command(self):
        return self.command.append(os.path.join(self.path_prefix, self.executable))

    def fairing_runtime_files(self):
        fairing_dir = os.path.dirname(fairing.__file__)
        ret = {}
        for f in ["__init__.py", "runtime_config.py"]:
            ret[os.path.join(fairing_dir, f)] = os.path.join(self.path_prefix, "fairing", f)
        return ret

# Reset the mtime on the the tarball for reproducibility
def reset_tar_mtime(tarinfo):
    tarinfo.mtime = 0
    return tarinfo
