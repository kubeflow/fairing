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

logging.basicConfig(level=logging.INFO)

# Basic model parameters as external flags.
FLAGS = None
parser = argparse.ArgumentParser()
parser.add_argument(
    '--max_steps',
    type=int,
    default=2000,
    help='Number of steps to run trainer.'
)
parser.add_argument(
    '--batch_size',
    type=int,
    default=100,
    help='Batch size.  Must divide evenly into the dataset sizes.'
)
parser.add_argument(
    '--input_data_dir',
    type=str,
    default=os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                          'tensorflow/mnist/input_data'),
    help='Directory to put the input data.'
)

 # HACK: Ideally we would want to have a unique subpath for each instance of the job, but since we can't
 # we are instead appending HOSTNAME to the logdir
parser.add_argument(
    '--log_dir',
    type=str,
    default=os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                          'tensorflow/mnist/logs/fully_connected_feed/', os.getenv('HOSTNAME', '')),
    help='Directory to put the log data.'
)
FLAGS, unparsed = parser.parse_known_args()

def placeholder_inputs(batch_size):
  images_placeholder = tf.placeholder(tf.float32, shape=(FLAGS.batch_size,
                                                         mnist.IMAGE_PIXELS))
  labels_placeholder = tf.placeholder(tf.int32, shape=(FLAGS.batch_size))
  return images_placeholder, labels_placeholder


def fill_feed_dict(data_set, images_pl, labels_pl):
  images_feed, labels_feed = data_set.next_batch(FLAGS.batch_size,
                                                 False)
  feed_dict = {
      images_pl: images_feed,
      labels_pl: labels_feed,
  }
  return feed_dict


def do_eval(sess,
            eval_correct,
            images_placeholder,
            labels_placeholder,
            data_set):
  # And run one epoch of eval.
  true_count = 0  # Counts the number of correct predictions.
  steps_per_epoch = data_set.num_examples // FLAGS.batch_size
  num_examples = steps_per_epoch * FLAGS.batch_size
  for step in xrange(steps_per_epoch):
    feed_dict = fill_feed_dict(data_set,
                               images_placeholder,
                               labels_placeholder)
    true_count += sess.run(eval_correct, feed_dict=feed_dict)
  precision = float(true_count) / num_examples
  print('Num examples: %d  Num correct: %d  Precision @ 1: %0.04f' %
        (num_examples, true_count, precision))


def gen_hyperparameters():
  return {
    'learning_rate': random.normalvariate(0.5, 0.5),
    'hidden1': np.random.choice([64, 128, 256], 1)[0],
    'hidden2': np.random.choice([16, 32, 64], 1)[0],
  }

@Train(
    backend = metaml.backend.Kubeflow,
    package={'name': 'mp-mnist', 'repository': 'wbuchwalter', 'publish': True},
    options={
      'hyper_parameters': gen_hyperparameters,
      'parallelism': 3
    },
    # resources={'gpu': 1},
    tensorboard={
      'log_dir': FLAGS.log_dir,
      'pvc_name': 'azurefile',
      'public': True
    }
)
def run_training(learning_rate, hidden1, hidden2):
  """Train MNIST for a number of steps."""
  print("Training with LR: {} and layer sizes: {}, {}".format(learning_rate, hidden1, hidden2))

  data_sets = input_data.read_data_sets(FLAGS.input_data_dir)

  with tf.Graph().as_default():
    images_placeholder, labels_placeholder = placeholder_inputs(
        FLAGS.batch_size)

    logits = mnist.inference(images_placeholder,
                             hidden1,
                             hidden2)

    loss = mnist.loss(logits, labels_placeholder)
    train_op = mnist.training(loss, learning_rate)
    eval_correct = mnist.evaluation(logits, labels_placeholder)
    summary = tf.summary.merge_all()
    init = tf.global_variables_initializer()
    saver = tf.train.Saver()
    sess = tf.Session()
    summary_writer = tf.summary.FileWriter(FLAGS.log_dir, sess.graph)
    sess.run(init)

    # Start the training loop.
    for step in xrange(FLAGS.max_steps):
      start_time = time.time()

      feed_dict = fill_feed_dict(data_sets.train,
                                 images_placeholder,
                                 labels_placeholder)

      _, loss_value = sess.run([train_op, loss],
                               feed_dict=feed_dict)

      duration = time.time() - start_time

      # Write the summaries and print an overview fairly often.
      if step % 100 == 0:
        print('Step %d: loss = %.2f (%.3f sec)' % (step, loss_value, duration))
        summary_str = sess.run(summary, feed_dict=feed_dict)
        summary_writer.add_summary(summary_str, step)
        summary_writer.flush()

      # Save a checkpoint and evaluate the model periodically.
      if (step + 1) % 1000 == 0 or (step + 1) == FLAGS.max_steps:
        checkpoint_file = os.path.join(FLAGS.log_dir, 'model.ckpt')
        saver.save(sess, checkpoint_file, global_step=step)
        # Evaluate against the training set.
        print('Training Data Eval:')
        do_eval(sess,
                eval_correct,
                images_placeholder,
                labels_placeholder,
                data_sets.train)
        # Evaluate against the validation set.
        print('Validation Data Eval:')
        do_eval(sess,
                eval_correct,
                images_placeholder,
                labels_placeholder,
                data_sets.validation)
        # Evaluate against the test set.
        print('Test Data Eval:')
        do_eval(sess,
                eval_correct,
                images_placeholder,
                labels_placeholder,
                data_sets.test)


def main(_):
  run_training()

  # if BACKEND == metaml.backend.Kubeflow:
  #   # Kubeflow delete pods as soon as they are completed, since it expects
  #   # that cluster logging is enabled. But this is not practical for demos,
  #   # So we sleep once the training is done to allow users to look at the pod's log
  #   import time
  #   time.sleep(1800)


if __name__ == '__main__':
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
  
