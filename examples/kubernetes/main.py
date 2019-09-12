# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
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


INPUT_DATA_DIR = '/tmp/tensorflow/mnist/input_data/'
MAX_STEPS = 2000
BATCH_SIZE = 100
LEARNING_RATE = 0.3
HIDDEN_1 = 128
HIDDEN_2 = 32

# HACK: Ideally we would want to have a unique subpath for each instance of the job,
# but since we can't, we are instead appending HOSTNAME to the logdir
LOG_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/logs/fully_connected_feed/', os.getenv('HOSTNAME', ''))


def train():
    data_sets = input_data.read_data_sets(INPUT_DATA_DIR)
    images_placeholder = tf.placeholder(
        tf.float32, shape=(BATCH_SIZE, mnist.IMAGE_PIXELS))
    labels_placeholder = tf.placeholder(tf.int32, shape=(BATCH_SIZE))

    logits = mnist.inference(images_placeholder,
                             HIDDEN_1,
                             HIDDEN_2)

    loss = mnist.loss(logits, labels_placeholder)
    train_op = mnist.training(loss, LEARNING_RATE)
    summary = tf.summary.merge_all()
    init = tf.global_variables_initializer()
    sess = tf.Session()
    summary_writer = tf.summary.FileWriter(LOG_DIR, sess.graph)
    sess.run(init)

    data_set = data_sets.train
    for step in xrange(MAX_STEPS):
        images_feed, labels_feed = data_set.next_batch(BATCH_SIZE, False)
        feed_dict = {
            images_placeholder: images_feed,
            labels_placeholder: labels_feed,
        }

        _, loss_value = sess.run([train_op, loss],
                                 feed_dict=feed_dict)
        if step % 100 == 0:
            print("At step {}, loss = {}".format(step, loss_value))
            summary_str = sess.run(summary, feed_dict=feed_dict)
            summary_writer.add_summary(summary_str, step)
            summary_writer.flush()


if __name__ == '__main__':
    if os.getenv('FAIRING_RUNTIME', None) is None:
        from kubeflow import fairing
        fairing.config.set_preprocessor('python', input_files=[__file__])
        fairing.config.set_builder('docker', registry='<your-registry-name>',
                                   base_image='tensorflow/tensorflow:1.13.1-py3')
        fairing.config.run()
    else:
        train()
