# import SimpleHTTPServer
# import SocketServer
# import socket
from metaparticle_pkg import Containerize

OK = 200

port = 8080

# class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
#     def do_GET(self):
#         self.send_response(OK)
#         self.send_header("Content-type", "text/plain")
#         self.end_headers()
#         self.wfile.write("Hello Metparticle [{}] @ {}\n".format(self.path, socket.gethostname()))
#         print("request for {}".format(self.path))
#     def do_HEAD(self):
#         self.send_response(OK)
#         self.send_header("Content-type", "text/plain")
#         self.end_headers()

@Containerize(
    package={
      'repository': 'wbuchwalter',
      'name': 'testwb'
    },
    runtime={
        'ports': [8080],
        'replicas': 4,
        'executor': 'metaparticle',
        'public': True
    })
def main():
    # Handler = MyHandler
    # httpd = SocketServer.TCPServer(("", port), Handler)
    # httpd.serve_forever()
    print("hey")

if __name__ == '__main__':
    main()