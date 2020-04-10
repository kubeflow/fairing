# Copyright 2020 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Trains and Evaluates the MNIST network using a feed dictionary."""
import os

from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.examples.tutorials.mnist import mnist
import tarfile
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

INPUT_DATA_DIR = '/tmp/tensorflow/mnist/input_data/'
MAX_STEPS = 500
BATCH_SIZE = 100
LEARNING_RATE = 0.3
HIDDEN_1 = 128
HIDDEN_2 = 32

# HACK: Ideally we would want to have a unique subpath for each instance of the job,
#  but since we can't, we are instead appending HOSTNAME to the logdir
LOG_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/logs/fully_connected_feed/', os.getenv('HOSTNAME', ''))


class MyModel():
    def __init__(self, endpoint_url, secret_id, secret_key, \
        region_name, bucket_name, blob_name):
        self.model_path = '/tmp/myModel/'
        if not os.path.exists(self.model_path):
            os.mkdir(self.model_path)
        self.model_tar_path = '/tmp/myModel.tar.gz'
        self.s3_endpoint_url = endpoint_url
        self.s3_secret_id = secret_id
        self.s3_secret_key = secret_key
        self.s3_region_name = region_name
        self.s3_bucket_name = bucket_name
        self.s3_blob_name = blob_name

    def train(self):
        self.data_sets = input_data.read_data_sets(INPUT_DATA_DIR)
        self.images_placeholder = tf.placeholder(
            tf.float32, shape=(BATCH_SIZE, mnist.IMAGE_PIXELS))
        self.labels_placeholder = tf.placeholder(tf.int32, shape=(BATCH_SIZE))

        logits = mnist.inference(self.images_placeholder,
                                 HIDDEN_1,
                                 HIDDEN_2)

        self.loss = mnist.loss(logits, self.labels_placeholder)
        self.train_op = mnist.training(self.loss, LEARNING_RATE)
        self.summary = tf.summary.merge_all()
        init = tf.global_variables_initializer()
        self.sess = tf.Session()
        self.summary_writer = tf.summary.FileWriter(LOG_DIR, self.sess.graph)
        self.sess.run(init)
        # train
        data_set = self.data_sets.train
        for step in xrange(MAX_STEPS):
            images_feed, labels_feed = data_set.next_batch(BATCH_SIZE, False)
            feed_dict = {
                self.images_placeholder: images_feed,
                self.labels_placeholder: labels_feed,
            }

            _, loss_value = self.sess.run([self.train_op, self.loss],
                                          feed_dict=feed_dict)
            if step % 100 == 0:
                print("At step {}, loss = {}".format(step, loss_value))
                summary_str = self.sess.run(self.summary, feed_dict=feed_dict)
                self.summary_writer.add_summary(summary_str, step)
                self.summary_writer.flush()
        # save
        saver = tf.train.Saver()
        save_path = saver.save(self.sess, self.model_path + 'model.pb')
        print('model saved to {}'.format(save_path))
        self.sess.close()

    def compress_model(self):
        tar = tarfile.open(self.model_tar_path, "w:gz")
        os.chdir(self.model_path)
        for name in os.listdir("."):
            tar.add(name)
        tar.close()
        print('model compressed to {}'.format(self.model_tar_path))

    def upload_model_to_s3(self):
        client = boto3.client('s3',
                              endpoint_url=self.s3_endpoint_url,
                              aws_access_key_id=self.s3_secret_id,
                              aws_secret_access_key=self.s3_secret_key,
                              config=Config(signature_version='s3v4'),
                              region_name=self.s3_region_name,
                              use_ssl=False)
        try:
            client.head_bucket(Bucket=self.s3_bucket_name)
        except ClientError:
            bucket = {'Bucket': self.s3_bucket_name}
            client.create_bucket(**bucket)
        client.upload_file(self.model_tar_path, self.s3_bucket_name, self.s3_blob_name)
        print('model uploaded to s3://{}/{}'.format(self.s3_bucket_name, self.s3_blob_name))


# To setup Minio, see
# https://docs.min.io/docs/minio-quickstart-guide.html
# To setup Minio Client, see
# https://docs.min.io/docs/minio-client-quickstart-guide.html
# To prepare docker config for Kanico, see
# https://github.com/GoogleContainerTools/kaniko#pushing-to-docker-hub

if __name__ == '__main__':
    image_registry = '<image-registry>'   # e.g. index.docker.io/XXXX
    s3_endpoint_url = '<s3-endpoint>'
    s3_secret_id = '<s3-secret-id>'
    s3_secret_key = '<s3-secret-key>'
    s3_region = '<s3-region>'
    s3_bucket_name = '<s3-bucket-name>'
    s3_blob_name = '<s3-blob-name>'

    if os.getenv('FAIRING_RUNTIME', None) is None:
        from kubeflow import fairing
        from kubeflow.fairing.builders.cluster.minio_context import MinioContextSource
        minio_context_source = MinioContextSource(
            endpoint_url=s3_endpoint_url,
            minio_secret=s3_secret_id,
            minio_secret_key=s3_secret_key,
            region_name=s3_region)

        fairing.config.set_preprocessor('python', input_files=[__file__, 'requirements.txt'])
        fairing.config.set_builder(
            name='cluster',
            registry=image_registry,
            context_source=minio_context_source,
            cleanup=True)
        fairing.config.run()
    else:
        remote_train = MyModel(s3_endpoint_url, s3_secret_id, s3_secret_key, \
            s3_region, s3_bucket_name, s3_blob_name)
        remote_train.train()
        remote_train.compress_model()
        remote_train.upload_model_to_s3()
