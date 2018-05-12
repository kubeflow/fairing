import json
import os
import subprocess


class Backend:
    def __init__(self):
        self.architecture = None
        self.strategy = None
        self.tensorboard_options = None
        self.serving_options = None

    def init_training(self, architecture, strategy, tensorboard_options):
        self.architecture = architecture
        self.strategy = strategy
        self.tensorboard_options = tensorboard_options
        self.validate_training()
    
    def init_serving(self, serving_options):
        self.serving_options = serving_options

    def cancel(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--delete'])

    def logs(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])
  
    def validate_training(self):
        # Todo: do common validation here  
        self.validate_training_options()
    
    def validate_training_options(self):
        raise NotImplementedError()
    
    def compile_training_ast(self, img, name):
      raise NotImplementedError()
    
    def compile_serving_ast(self, img, name):
      raise NotImplementedError()

    def run_serving(self, img, name):
        svc = self.compile_serving_ast(img, name)
        self.run(svc)

    def run_training(self, img, name):
        svc = self.compile_training_ast(img, name)
        self.run(svc)
    
    def run(self, svc):
        if not os.path.exists('.metaparticle'):
            os.makedirs('.metaparticle')

        with open('.metaparticle/spec.json', 'w') as out:
            json.dump(svc, out)
        
        subprocess.check_call(['mp-compiler', '-f', '.metaparticle/spec.json'])     