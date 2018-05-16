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
import tensorflow as tf
import numpy as np

from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.examples.tutorials.mnist import mnist

import metaml.backend
from metaml.train import Train
from metaml.strategies.pbt import PopulationBasedTraining

# logging.basicConfig(level=logging.INFO)

INPUT_DATA_DIR = '/tmp/tensorflow/mnist/input_data/'
MAX_STEPS = 2000
BATCH_SIZE = 100

# HACK: Ideally we would want to have a unique subpath for each instance of the job, but since we can't
# we are instead appending HOSTNAME to the logdir
LOG_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/logs/fully_connected_feed/', os.getenv('HOSTNAME', ''))
MODEL_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                       'tensorflow/mnist/models/fully_connected_feed/', os.getenv('HOSTNAME', ''), 'model.ckpt')


def placeholder_inputs(batch_size):
    images_placeholder = tf.placeholder(tf.float32, shape=(BATCH_SIZE,
                                                           mnist.IMAGE_PIXELS))
    labels_placeholder = tf.placeholder(tf.int32, shape=(BATCH_SIZE))
    return images_placeholder, labels_placeholder


def fill_feed_dict(data_set, images_pl, labels_pl):
    images_feed, labels_feed = data_set.next_batch(BATCH_SIZE,
                                                   False)
    feed_dict = {
        images_pl: images_feed,
        labels_pl: labels_feed,
    }
    return feed_dict


def gen_hyperparameters():
    return {
        'learning_rate': random.uniform(0.001, 1)
    }


# saver = tf.train.Saver()
data_sets = input_data.read_data_sets(INPUT_DATA_DIR)

first_run = True

images_placeholder = None
labels_placeholder = None
train_op = None
loss = None

@Train(
    package={'name': 'metaml-pbt', 'repository': 'wbuchwalter', 'publish': True},
    strategy=PopulationBasedTraining(
        hyperparameters=gen_hyperparameters,
        model_dir=MODEL_DIR,
        population_size=3,
        exploit_count=15,
        steps_per_exploit=5000,
        pvc_name= 'azurefile2'
    ),
    tensorboard={
        'log_dir': LOG_DIR,
        'pvc_name': 'azurefile',
        'public': True
    }
)
def run_training(sess, graph, max_steps, reporter, learning_rate):
    global images_placeholder
    global labels_placeholder
    global train_op
    global loss
    global first_run
    with graph.as_default():
        if first_run:
            hidden1 = 128
            hidden2 = 32
            # with tf.Graph().as_default():
            images_placeholder, labels_placeholder = placeholder_inputs(
                BATCH_SIZE)

            logits = mnist.inference(images_placeholder,
                                        hidden1,
                                        hidden2)

            loss = mnist.loss(logits, labels_placeholder)
            train_op = mnist.training(loss, learning_rate)
            eval_correct = mnist.evaluation(logits, labels_placeholder)
            summary = tf.summary.merge_all()
            # Todo: init should happen only once
            init = tf.global_variables_initializer()
            saver = tf.train.Saver()
            # sess = tf.Session()
            summary_writer = tf.summary.FileWriter(LOG_DIR, sess.graph)
            sess.run(init)
            first_run = False

        # Start the training loop.
        for step in xrange(max_steps):
            start_time = time.time()

            feed_dict = fill_feed_dict(data_sets.train,
                                        images_placeholder,
                                        labels_placeholder)

            _, loss_value = sess.run([train_op, loss],
                                        feed_dict=feed_dict)
        reporter(loss_value, saver, sess)


def main(_):
    run_training()


if __name__ == '__main__':
    tf.app.run(main=main, argv=[sys.argv[0]])
