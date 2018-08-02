import signal
import sys
import shutil
import http.server
import logging

from fairing.backend import NativeBackend
from fairing.docker import is_in_docker_container, DockerBuilder
from fairing.options import PackageOptions
import fairing.metaparticle as mp

logger = logging.getLogger('fairing')

user_function = None
serving_route = None


class Serve(object):

    def __init__(self, package, route='/predict', port=8080, replicas=1):
        global serving_route
        serving_route = route

        # For now we force native backend for serving,
        # we might want to give more option later, i.e using seldon + kubeflow
        self.backend = NativeBackend()
        self.route = route
        self.port = port
        self.replicas = replicas
        self.package = PackageOptions(**package)
        self.image = "{repo}/{name}:latest".format(
            repo=self.package.repository,
            name=self.package.name
        )

        self.builder = DockerBuilder()

    def __call__(self, func):
        def wrapped():
            if is_in_docker_container():
                return self.serve(func)

            exec_file = sys.argv[0]
            slash_ix = exec_file.find('/')
            if slash_ix != -1:
                exec_file = exec_file[slash_ix:]

            ast = self.backend.compile_serving_ast(
                self.image, self.package.name, self.port, self.replicas)

            self.builder.write_dockerfile(self.package, exec_file)
            self.builder.build(self.image)

            if self.package.publish:
                self.builder.publish(self.image)

            def signal_handler(signal, frame):
                mp.cancel(self.package.name)
                sys.exit(0)
            signal.signal(signal.SIGINT, signal_handler)

            mp.run(ast)
            print("Server deployed.")

            return mp.logs(self.package.name)
        return wrapped

    def serve(self, func):
        global user_function
        user_function = func
        # TODO: Serve only on url passed to decorator + port
        httpd = http.server.HTTPServer(('', self.port), HTTPHandler)
        print('Server running on port 8080...')
        httpd.serve_forever()


class HTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == serving_route:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # TODO: Handle parameters + error catching
            res = user_function()
            self.wfile.write(bytes(res, "utf8"))
        return
