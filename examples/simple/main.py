import os
import tensorflow as tf

from kubeflow import fairing
# Setting up google container repositories (GCR) for storing output containers
# You can use any docker container registry istead of GCR
GCP_PROJECT = fairing.cloud.gcp.guess_project_name()
DOCKER_REGISTRY = 'gcr.io/{}/fairing-job'.format(GCP_PROJECT)
fairing.config.set_builder(
    'append', base_image='tensorflow/tensorflow:1.13.1-py3', registry=DOCKER_REGISTRY, push=True)
fairing.config.set_deployer('job')


def train():
    hostname = tf.constant(os.environ['HOSTNAME'])
    sess = tf.Session()
    print('Hostname: ', sess.run(hostname).decode('utf-8'))


if __name__ == '__main__':
    remote_train = fairing.config.fn(train)
    remote_train()
