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
import argparse
import os
import sys
import time
import random
import logging

from six.moves import xrange  # pylint: disable=redefined-builtin
import numpy as np
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.examples.tutorials.mnist import mnist

from metaml.train import Train
from metaml.strategies.hp import HyperparameterTuning

INPUT_DATA_DIR = '/tmp/tensorflow/mnist/input_data/'
MAX_STEPS = 2000
# HACK: Ideally we would want to have a unique subpath for each instance of the job, but since we can't
# we are instead appending HOSTNAME to the logdir
LOG_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/logs/fully_connected_feed/', os.getenv('HOSTNAME', ''))
MODEL_DIR = os.path.join(LOG_DIR, 'model.ckpt')

# logging.basicConfig(level=logging.DEBUG)


@Train(
    package={'name': 'metaml-hp-tuning', 'repository': '<your-repository>', 'publish': True},
    strategy=HyperparameterTuning(runs=3),
    tensorboard={
        'log_dir': LOG_DIR,
        'pvc_name': '<pvc-name>',
        'public': True
    }
)
class MyModel(object):
    def hyperparameters(self):
        return {
            'learning_rate': random.normalvariate(0.5, 0.45),
            'batch_size':  np.random.choice([10, 50, 100], 1)[0],
            'hidden1': np.random.choice([64, 128, 256], 1)[0],
            'hidden2': np.random.choice([16, 32, 64], 1)[0],
        }

    def build(self, hp):
        self.data_sets = input_data.read_data_sets(INPUT_DATA_DIR)
        self.images_placeholder = tf.placeholder(
            tf.float32, shape=(hp['batch_size'], mnist.IMAGE_PIXELS))
        self.labels_placeholder = tf.placeholder(
            tf.int32, shape=(hp['batch_size']))

        logits = mnist.inference(self.images_placeholder,
                                 hp['hidden1'],
                                 hp['hidden2'])

        self.loss = mnist.loss(logits, self.labels_placeholder)
        self.train_op = mnist.training(self.loss, hp['learning_rate'])
        self.summary = tf.summary.merge_all()
        init = tf.global_variables_initializer()
        saver = tf.train.Saver()
        self.sess = tf.Session()
        self.summary_writer = tf.summary.FileWriter(LOG_DIR, self.sess.graph)
        self.sess.run(init)

    def train(self, hp):
        print('Starting training with learning_rate: {}, batch_size: {}, layer1: {}, layer2: {}.'.format(
            hp['learning_rate'],
            hp['batch_size'],
            hp['hidden1'],
            hp['hidden2']
        ))
        data_set = self.data_sets.train
        for step in xrange(MAX_STEPS):
            images_feed, labels_feed = data_set.next_batch(
                hp['batch_size'], False)
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

if __name__ == '__main__':
    model = MyModel()
    model()
