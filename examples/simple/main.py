import os
import fairing
import tensorflow as tf

fairing.config.set_builder('docker', push=False)
fairing.config.set_deployer('job')

def train():
    hostname = tf.constant(os.environ['HOSTNAME'])
    sess = tf.Session()
    print('Hostname: ', sess.run(hostname).decode('utf-8'))

if __name__ == '__main__':
    remote_train = fairing.config.fn(train)
    remote_train()
