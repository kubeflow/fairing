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
  
    def validate_training(self, train_options, tensorboard_options):
        # Todo: do common validation here  
        self.validate_training_options(train_options, tensorboard_options)
    
    def validate_training_options(self, train_options, tensorboard_options):
        raise NotImplementedError()
    
    def compile_training_ast(self, img, name, train_options, tensorboard_options):
      raise NotImplementedError()
    
    def compile_serving_ast(self, img, name, serving_options):
      raise NotImplementedError()

    def run_serving(self, img, name, serving_options):
        svc = self.compile_serving_ast(img, name, serving_options)
        self.run(svc)

    def run_training(self, img, name, train_options, tensorboard_options):
        svc = self.compile_training_ast(img, name, train_options, tensorboard_options)
        self.run(svc)
    
    def run(self, svc):
        if not os.path.exists('.metaparticle'):
            os.makedirs('.metaparticle')

        with open('.metaparticle/spec.json', 'w') as out:
            json.dump(svc, out)
        
        subprocess.check_call(['mp-compiler', '-f', '.metaparticle/spec.json'])     