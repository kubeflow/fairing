import os
import sys
import shutil

from fairing.notebook_helper import get_notebook_name, is_in_notebook

class DockerFile(object):
    
    def get_exec_file_name(self):
        exec_file = sys.argv[0]
        slash_ix = exec_file.find('/')
        if slash_ix != -1:
            exec_file = exec_file[slash_ix + 1:]
        return exec_file

    def get_command(self):
        exec_file = ''
        if is_in_notebook():
            nb_name = get_notebook_name()
            exec_file = nb_name.replace('.ipynb', '.py')
        else:
          exec_file = self.get_exec_file_name()

        return "CMD python /app/{exec_file}".format(exec_file=exec_file)

    def get_base_image(self):
        if os.environ.get('FAIRING_DEV', None) != None:
            try:
                uname = os.environ['FAIRING_DEV_DOCKER_USERNAME']
            except KeyError:
                raise KeyError("FAIRING_DEV environment variable is defined but "
                               "FAIRING_DEV_DOCKER_USERNAME is not. Either set "
                               "FAIRING_DEV_DOCKER_USERNAME to your Docker hub username, "
                               "or set FAIRING_DEV to false.")
            return '{uname}/fairing:latest'.format(uname=uname)
        return 'library/python:3.6'

    def generate_dockerfile(self, env):
        all_steps = ['FROM {}'.format(self.get_base_image())] + \
                    self.get_mandatory_steps() + \
                    self.get_env_steps(env) + \
                    [self.get_command()]
    
        return '\n'.join(all_steps)

    def get_mandatory_steps(self):
        steps = [
            "ENV FAIRING_RUNTIME 1",
            "RUN pip install fairing",
            "COPY ./ /app/",
            "RUN pip install --no-cache -r /app/requirements.txt"
        ]

        if is_in_notebook():
            nb_name = get_notebook_name()
            steps += [
                "RUN pip install jupyter nbconvert",
                "RUN jupyter nbconvert --to script /app/{}".format(nb_name)
            ]
        return steps

    def get_env_steps(self, env):
        if env:
            return ["ENV {} {}".format(e['name'], e['value']) for e in env]
        return []
    
    def write(self, package, env, destination='Dockerfile'):
        if hasattr(package, 'dockerfile') and package.dockerfile is not None:
            shutil.copy(package.dockerfile, destination)
            return       
        
        content =  self.generate_dockerfile(env)
        with open(destination, 'w+t') as f:
            f.write(content)

