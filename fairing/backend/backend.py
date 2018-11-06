import json
import os
import subprocess


class Backend:
    def add_tensorboard(self, svc, name, tensorboard_options):
        raise NotImplementedError()

    def compile_serving_ast(self, img, name, port, replicas):
        raise NotImplementedError()

    def stream_logs(self, image_name, image_tag):
        raise NotImplementedError()