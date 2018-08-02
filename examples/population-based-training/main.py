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

from fairing.train import Train
from fairing.strategies.pbt import PopulationBasedTraining
from fairing.strategies.pbt.explore import Perturb

INPUT_DATA_DIR = '/tmp/tensorflow/mnist/input_data/'
MAX_STEPS = 2000
# HACK: Ideally we would want to have a unique subpath for each instance of the job, but since we can't
# we are instead appending HOSTNAME to the logdir
LOG_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/logs/fully_connected_feed/', os.getenv('HOSTNAME', ''))
MODEL_DIR = os.path.join(LOG_DIR, os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/models/fully_connected_feed/', os.getenv('HOSTNAME', ''), 'model.ckpt')

# logging.basicConfig(level=logging.DEBUG)

@Train(
    package={'name': 'fairing-pbt', 'repository': '<your-repository>', 'publish': True},
    strategy=PopulationBasedTraining(
        population_size=10,
        exploit_count=4,
        steps_per_exploit=5000,
        pvc_name='<pvc2-name>',
        model_path = MODEL_DIR
    ),
    tensorboard={
        'log_dir': LOG_DIR,
        'pvc_name': '<pvc-name>',
        'public': True
    }
)
class MyModel(object):
    def __init__(self):
        self.global_step = 0

    def hyperparameters(self):
        return {
            'learning_rate': np.random.choice([0.01, 0.1, 1, 10, 100], 1)[0].item(),
            'batch_size':  50,
            'hidden1': 128,
            'hidden2': 32,
        }

    def build(self, hp):
        with tf.Graph().as_default():
          tf.summary.scalar('lr', hp['learning_rate'])
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
          self.saver = tf.train.Saver()
          self.sess = tf.Session()
          self.summary_writer = tf.summary.FileWriter(LOG_DIR, self.sess.graph)
          self.sess.run(init)

    def train(self, steps, reporter, hp):
        print('training with lr: {}'.format(hp['learning_rate']))
        data_set = self.data_sets.train
        for step in xrange(steps):
            self.global_step += 1
            images_feed, labels_feed = data_set.next_batch(
                hp['batch_size'], False)
            feed_dict = {
                self.images_placeholder: images_feed,
                self.labels_placeholder: labels_feed,
            }

            _, loss_value = self.sess.run([self.train_op, self.loss],
                                          feed_dict=feed_dict)
            if step % 100 == 0:
                print("At step {}, loss = {}".format(self.global_step, loss_value))
                summary_str = self.sess.run(self.summary, feed_dict=feed_dict)
                self.summary_writer.add_summary(summary_str, self.global_step)
                self.summary_writer.flush()
        reporter(loss_value)
        

    def save(self):
        self.saver.save(self.sess, MODEL_DIR)
        pass

    def restore(self, model_path):
        self.saver.restore(self.sess, model_path)
        pass


if __name__ == '__main__':
    model = MyModel()
    model()
