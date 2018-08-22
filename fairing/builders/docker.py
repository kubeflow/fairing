import shutil
import os
import json
import logging
import sys

from docker import APIClient

from fairing.notebook import get_notebook_name, is_in_notebook
from fairing.builders.container_image_builder import ContainerImageBuilder
from fairing.utils import get_image

logger = logging.getLogger('fairing')


def get_exec_file_name():
    exec_file = sys.argv[0]
    slash_ix = exec_file.find('/')
    if slash_ix != -1:
        exec_file = exec_file[slash_ix + 1:]
    return exec_file


class DockerFile(object):
    def __init__(self):
        self.steps = []
        self.cmd = ''

    def get_base_image(self):
        if os.environ.get('FAIRING_DEV', None) != None:
            try:
                uname =  os.environ['FAIRING_DEV_DOCKER_USERNAME']
            except KeyError:
                raise KeyError("FAIRING_DEV environment variable is defined but "
                                "FAIRING_DEV_DOCKER_USERNAME is not. Either set " 
                                "FAIRING_DEV_DOCKER_USERNAME to your Docker hub username, "
                                "or set FAIRING_DEV to false.")
            return '{uname}/fairing:latest'.format(uname=uname)
        return 'library/python:3.6'
    
    def add_step(self, step):
        self.steps.append(step)
    
    def add_steps(self, steps):
        [self.steps.append(step) for step in steps]
    
    def set_cmd(self, cmd):
        self.cmd = cmd

    def build_dockerfile(self):
        all_steps = ['FROM {}'.format(self.get_base_image())] + self.steps + [self.cmd]
        return '\n'.join(all_steps)

class DockerBuilder(ContainerImageBuilder):
    def __init__(self):
        self.docker_client = None
        self.dockerfile = DockerFile()
  
    def execute(self, package_options, env):
        image = get_image(package_options)
        self.write_dockerfile(package_options, env)
        self.build(image)
        if package_options.publish:
            self.publish(image)

    def write_dockerfile(self, package, env, dockerfile_path='Dockerfile'):
        if hasattr(package, 'dockerfile') and package.dockerfile is not None:
            shutil.copy(package.dockerfile, 'Dockerfile')
            return       
        
        content = self.generate_dockerfile_content(env)
        with open(dockerfile_path, 'w+t') as f:
            f.write(content)

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
        return ["ENV {} {}".format(e['name'], e['value']) for e in env]

    def generate_dockerfile_content(self, env):
        self.dockerfile.add_steps(self.get_mandatory_steps())
        self.dockerfile.add_steps(self.get_env_steps())
        self.dockerfile.set_cmd("CMD python /app/{exec_file}".format(exec_file=self.get_entry_point()))
        return self.dockerfile.build_dockerfile()

    def get_entry_point(self):
        if is_in_notebook():
            nb_name = get_notebook_name()
            return  nb_name.replace('.ipynb', '.py')
        return get_exec_file_name()

    def build(self, img, path='.'):
        print('Building docker image {}...'.format(img))
        if self.docker_client is None:
            self.docker_client = APIClient(version='auto')

        bld = self.docker_client.build(
            path=path,
            tag=img,
            encoding='utf-8'
        )

        for line in bld:
            self._process_stream(line)

    def publish(self, img):
        print('Publishing image {}...'.format(img))
        if self.docker_client is None:
            self.docker_client = APIClient(version='auto')

        # TODO: do we need to set tag?
        for line in self.docker_client.push(img, stream=True):
            self._process_stream(line)

    def _process_stream(self, line):
        raw = line.decode('utf-8').strip()
        lns = raw.split('\n')
        for ln in lns:
            # try to decode json
            try:
                ljson = json.loads(ln)

                if ljson.get('error'):
                    msg = str(ljson.get('error', ljson))
                    logger.error('Build failed: ' + msg)
                    raise Exception('Image build failed: ' + msg)
                else:
                    if ljson.get('stream'):
                        msg = 'Build output: {}'.format(
                            ljson['stream'].strip())
                    elif ljson.get('status'):
                        msg = 'Push output: {} {}'.format(
                            ljson['status'],
                            ljson.get('progress')
                        )
                    elif ljson.get('aux'):
                        msg = 'Push finished: {}'.format(ljson.get('aux'))
                    else:
                        msg = str(ljson)
                    logger.info(msg)

            except json.JSONDecodeError:
                logger.warning('JSON decode error: {}'.format(ln))
