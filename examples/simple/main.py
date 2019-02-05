import os
import fairing
import tensorflow as tf

class SimpleModel():
    def train(self):
        hostname = tf.constant(os.environ['HOSTNAME'])
        sess = tf.Session()
        print('Hostname: ', sess.run(hostname).decode('utf-8'))

fairing.config.set_model(SimpleModel())
fairing.config.run()