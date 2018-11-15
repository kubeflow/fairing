import json
import os
import subprocess


class Backend:
    def add_tensorboard(self, svc, name, tensorboard_options):
        raise NotImplementedError()

    def stream_logs(self, image_name, image_tag):
        raise NotImplementedError()