import signal
import sys
import shutil
import http.server
import logging

from metaml.backend import get_backend, Native
from metaml.docker import is_in_docker_container, DockerBuilder
from metaml.options import PackageOptions, ServeOptions

logger = logging.getLogger('metaml')

user_function = None

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

            self.builder.write_dockerfile(self.package, exec_file)
            self.builder.build(self.image)

            if self.package.publish:
                self.builder.publish(self.image)

            def signal_handler(signal, frame):
                self.backend.cancel(self.package.name)
                sys.exit(0)
            signal.signal(signal.SIGINT, signal_handler)

            self.backend.run_serving(
                self.image, self.package.name, self.serve_options)
            print("Server deployed.")

            return self.backend.logs(self.package.name)
        return wrapped

    def serve(self, func):
        global user_function
        user_function = func
        # TODO: Serve only on url passed to decorator + port
        httpd = http.server.HTTPServer(('', 8080), HTTPHandler)
        print('Server running on port 8080...')
        httpd.serve_forever()


class HTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        #TODO: Handle parameters + error catching
        res = user_function()
        self.wfile.write(bytes(res, "utf8"))
        return
