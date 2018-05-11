import shutil
import os

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

def write_dockerfile(package, exec_file):
    if hasattr(package, 'dockerfile') and package.dockerfile is not None:
        shutil.copy(package.dockerfile, 'Dockerfile')
        return

    with open('Dockerfile', 'w+t') as f:
        f.write("""FROM wbuchwalter/metaml

COPY ./ /app/
RUN pip install --no-cache -r /app/requirements.txt

CMD python /app/{exec_file}
""".format(version=package.py_version, exec_file=exec_file))