import signal
import sys
import shutil

from flask import Flask

from metaml.backend import get_backend, Native
from metaml.docker import is_in_docker_container, DockerBuilder
from metaml.options import PackageOptions, ServeOptions

class Serve(object):

  def __init__(self, package, serve_options={}, backend=Native):
    self.backend = backend
    self.serve_options = ServeOptions(**serve_options)
    self.package = PackageOptions(**package)
    self.image = "{repo}/{name}:latest".format(
          repo=self.package.repository,
          name=self.package.name
      )

    self.builder = DockerBuilder()
    self.backend = get_backend(backend)

  def __call__(self, func):
    def wrapped():
      if is_in_docker_container():
        return self.serve(func)

      exec_file = sys.argv[0]
      slash_ix = exec_file.find('/')
      if slash_ix != -1:
        exec_file = exec_file[slash_ix:]

      self.write_dockerfile(self.package, exec_file)
      self.builder.build(self.image)

      if self.package.publish:
        self.builder.publish(self.image)

      def signal_handler(signal, frame):
        self.backend.cancel(self.package.name)
        sys.exit(0)
      signal.signal(signal.SIGINT, signal_handler)

      # TODO: pass args
      self.backend.run_serving(self.image, self.package.name, self.serve_options)
      print("Serve it it like it's hot.")

      return self.backend.logs(self.package.name)
    return wrapped

  def serve(self, func):
    # TODO: route is not registered
    app.add_url_rule('/', view_func=func)

  def write_dockerfile(self, package, exec_file):
    if hasattr(package, 'dockerfile') and package.dockerfile is not None:
        shutil.copy(package.dockerfile, 'Dockerfile')
        return

    with open('Dockerfile', 'w+t') as f:
        f.write("""FROM wbuchwalter/metaml
RUN pip install flask

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY ./ /app/
WORKDIR /app
RUN pip install --no-cache -r /app/requirements.txt
ENV FLASK_APP={exec_file}

# This is gross
# Todo: find a less gross way to create the flask app
RUN sed -i '1s;^;from flask import Flask\napp = Flask(__name__)\n;'  {exec_file}
CMD flask run -h 0.0.0.0
""".format(version=package.py_version, exec_file=exec_file))




