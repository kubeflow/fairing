import json
import os
import subprocess


class Backend:
    def cancel(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--delete'])

    def logs(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])

    def compile_ast(self, img, name, train_options, tensorboard_options):
      raise NotImplementedError()
    
     