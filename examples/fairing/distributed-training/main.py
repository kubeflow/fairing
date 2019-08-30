# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A simple MNIST classifier which displays summaries in TensorBoard.

This is an unimpressive MNIST model, but it is a good example of using
tf.name_scope to make a graph legible in the TensorBoard graph explorer, and of
naming summary tags so that they are grouped meaningfully in TensorBoard.

It demonstrates the functionality of every TensorBoard dashboard.
"""

import os
import json

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data


MAX_STEPS = 1000
LEARNING_RATE = 0.001
DROPOUT = 0.9
DATA_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'),
                        'tensorflow/input_data')
LOG_DIR = os.path.join(os.getenv('TEST_TMPDIR', '/tmp'), 'tensorflow/logs')


class TensorflowModel(object):
    def build(self):  # pylint:disable=too-many-statements
        tf_config_json = os.environ.get("TF_CONFIG", "{}")
        tf_config = json.loads(tf_config_json)

        task = tf_config.get("task", {})
        cluster_spec = tf_config.get("cluster", {})
        cluster_spec_object = tf.train.ClusterSpec(cluster_spec)
        job_name = task["type"]
        task_id = task["index"]
        server_def = tf.train.ServerDef(
            cluster=cluster_spec_object.as_cluster_def(),
            protocol="grpc",
            job_name=job_name,
            task_index=task_id)
        self.server = tf.train.Server(server_def)
        self.is_chief = (job_name == 'chief' or job_name == 'master')

        # Import data
        self.mnist = input_data.read_data_sets(DATA_DIR, one_hot=True)

        # Between-graph replication
        with tf.device(tf.train.replica_device_setter(
            worker_device="/job:worker/task:%d" % task_id,
            cluster=cluster_spec)):

            # count the number of updates
            self.global_step = tf.get_variable(
                'global_step',
                [],
                initializer=tf.constant_initializer(0),
                trainable=False)

            # Input placeholders
            with tf.name_scope('input'):
                self.x = tf.placeholder(
                    tf.float32, [None, 784], name='x-input')
                self.y_ = tf.placeholder(
                    tf.float32, [None, 10], name='y-input')

            with tf.name_scope('input_reshape'):
                image_shaped_input = tf.reshape(self.x, [-1, 28, 28, 1])
                tf.summary.image('input', image_shaped_input, 10)

            # We can't initialize these variables to 0 - the network will get stuck.
            def weight_variable(shape):
                """Create a weight variable with appropriate initialization."""
                initial = tf.truncated_normal(shape, stddev=0.1)
                return tf.Variable(initial)

            def bias_variable(shape):
                """Create a bias variable with appropriate initialization."""
                initial = tf.constant(0.1, shape=shape)
                return tf.Variable(initial)

            def variable_summaries(var):
                """Attach a lot of summaries to a Tensor (for TensorBoard visualization)."""
                with tf.name_scope('summaries'):
                    mean = tf.reduce_mean(var)
                    tf.summary.scalar('mean', mean)
                    with tf.name_scope('stddev'):
                        stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
                    tf.summary.scalar('stddev', stddev)
                    tf.summary.scalar('max', tf.reduce_max(var))
                    tf.summary.scalar('min', tf.reduce_min(var))
                    tf.summary.histogram('histogram', var)

            def nn_layer(input_tensor, input_dim, output_dim, layer_name, act=tf.nn.relu):
                """Reusable code for making a simple neural net layer.

                It does a matrix multiply, bias add, and then uses ReLU to nonlinearize.
                It also sets up name scoping so that the resultant graph is easy to read,
                and adds a number of summary ops.
                """
                # Adding a name scope ensures logical grouping of the layers in the graph.
                with tf.name_scope(layer_name):
                    # This Variable will hold the state of the weights for the layer
                    with tf.name_scope('weights'):
                        weights = weight_variable([input_dim, output_dim])
                        variable_summaries(weights)
                    with tf.name_scope('biases'):
                        biases = bias_variable([output_dim])
                        variable_summaries(biases)
                    with tf.name_scope('Wx_plus_b'):
                        preactivate = tf.matmul(input_tensor, weights) + biases
                        tf.summary.histogram('pre_activations', preactivate)
                    activations = act(preactivate, name='activation')
                    tf.summary.histogram('activations', activations)
                    return activations

            hidden1 = nn_layer(self.x, 784, 500, 'layer1')

            with tf.name_scope('dropout'):
                self.keep_prob = tf.placeholder(tf.float32)
                tf.summary.scalar('dropout_keep_probability', self.keep_prob)
                dropped = tf.nn.dropout(hidden1, self.keep_prob)

            # Do not apply softmax activation yet, see below.
            y = nn_layer(dropped, 500, 10, 'layer2', act=tf.identity)

            with tf.name_scope('cross_entropy'):
                # The raw formulation of cross-entropy,
                #
                # tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(tf.softmax(y)),
                #                               reduction_indices=[1]))
                #
                # can be numerically unstable.
                #
                # So here we use tf.nn.softmax_cross_entropy_with_logits on the
                # raw outputs of the nn_layer above, and then average across
                # the batch.
                diff = tf.nn.softmax_cross_entropy_with_logits(
                    labels=self.y_, logits=y)
                with tf.name_scope('total'):
                    cross_entropy = tf.reduce_mean(diff)
            tf.summary.scalar('cross_entropy', cross_entropy)

            with tf.name_scope('train'):
                self.train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(
                    cross_entropy)

            with tf.name_scope('accuracy'):
                with tf.name_scope('correct_prediction'):
                    correct_prediction = tf.equal(
                        tf.argmax(y, 1), tf.argmax(self.y_, 1))
                with tf.name_scope('accuracy'):
                    self.accuracy = tf.reduce_mean(
                        tf.cast(correct_prediction, tf.float32))
            tf.summary.scalar('accuracy', self.accuracy)

            # Merge all the summaries and write them out to
            # /tmp/tensorflow/mnist/logs/mnist_with_summaries (by default)
            self.merged = tf.summary.merge_all()

            self.init_op = tf.global_variables_initializer()

    def train(self):
        self.build()

        def feed_dict(train):
            """Make a TensorFlow feed_dict: maps data onto Tensor placeholders."""
            if train:
                xs, ys = self.mnist.train.next_batch(100, fake_data=False)
                k = DROPOUT
            else:
                xs, ys = self.mnist.test.images, self.mnist.test.labels
                k = 1.0
            return {self.x: xs, self.y_: ys, self.keep_prob: k}

        sv = tf.train.Supervisor(is_chief=self.is_chief,
                                 global_step=self.global_step,
                                 init_op=self.init_op,
                                 logdir=LOG_DIR)

        with sv.prepare_or_wait_for_session(self.server.target) as sess:
            train_writer = tf.summary.FileWriter(
                LOG_DIR + '/train', sess.graph)
            test_writer = tf.summary.FileWriter(LOG_DIR + '/test')
            # Train the model, and also write summaries.
            # Every 10th step, measure test-set accuracy, and write test summaries
            # All other steps, run train_step on training data, & add training summaries

            for i in range(MAX_STEPS):
                if i % 10 == 0:  # Record summaries and test-set accuracy
                    summary, acc = sess.run(
                        [self.merged, self.accuracy], feed_dict=feed_dict(False))
                    test_writer.add_summary(summary, i)
                    print('Accuracy at step %s: %s' % (i, acc))
                else:  # Record train set summaries, and train
                    if i % 100 == 99:  # Record execution stats
                        run_options = tf.RunOptions(
                            trace_level=tf.RunOptions.FULL_TRACE)
                        run_metadata = tf.RunMetadata()
                        summary, _ = sess.run([self.merged, self.train_step],
                                              feed_dict=feed_dict(True),
                                              options=run_options,
                                              run_metadata=run_metadata)
                        train_writer.add_run_metadata(
                            run_metadata, 'step%03d' % i)
                        train_writer.add_summary(summary, i)
                        print('Adding run metadata for', i)
                    else:  # Record a summary
                        summary, _ = sess.run(
                            [self.merged, self.train_step], feed_dict=feed_dict(True))
                        train_writer.add_summary(summary, i)
            train_writer.close()
            test_writer.close()


if __name__ == '__main__':
    if os.getenv('FAIRING_RUNTIME', None) is None:
        from kubeflow import fairing
        fairing.config.set_preprocessor('python', input_files=[__file__])
        fairing.config.set_builder(
            name='docker', registry='gcr.io/mrick-gcp', base_image='tensorflow/tensorflow')
        fairing.config.set_deployer(
            name='tfjob', namespace='default', worker_count=1, ps_count=1)
        fairing.config.run()
    else:
        remote_train = TensorflowModel()
        remote_train.train()
