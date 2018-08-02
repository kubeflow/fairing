import shutil
import os
import json
import logging

from docker import APIClient
logger = logging.getLogger('fairing')

def is_in_docker_container():
  mp_in_container = os.getenv('METAPARTICLE_IN_CONTAINER', None)
  if mp_in_container in ['true', '1']:
      return True
  elif mp_in_container in ['false', '0']:
      return False

  try:
      with open('/proc/1/cgroup', 'r+t') as f:
          lines = f.read().splitlines()
          last_line = lines[-1]
          if 'docker' in last_line:
              return True
          elif 'kubepods' in last_line:
              return True
          else:
              return False

  except IOError:
      return False


class DockerBuilder:
    def __init__(self):
        self.docker_client = None
    
    def write_dockerfile(self, package, exec_file, env):
        if hasattr(package, 'dockerfile') and package.dockerfile is not None:
            shutil.copy(package.dockerfile, 'Dockerfile')
            return
        env = env if env else []
        env_str = ""
        for e in env:
            env_str += "ENV {} {} \n".format(e['name'], e['value'])

        with open('Dockerfile', 'w+t') as f:
            f.write("""FROM library/python:3.6
COPY ./ /app/
RUN pip install --no-cache -r /app/requirements.txt
{env_str}
CMD python /app/{exec_file}
""".format(version=package.py_version, exec_file=exec_file, env_str=env_str))


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
                        msg = 'Build output: {}'.format(ljson['stream'].strip())
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