
import logging
import types
import redis
import os
import json
import math
import numpy as np

from ..basic import BasicTrainingStrategy
from .exploit import Truncation
from .explore import Resample
from metaml.docker import is_in_docker_container

#TODO: can we make this class framework agnostic?
if is_in_docker_container():
    import tensorflow as tf

logger = logging.getLogger('metaml')

class PopulationBasedTraining(BasicTrainingStrategy):
    def __init__(self,
                 hyperparameters,
                 #  saver,           # used to restore model
                 model_dir,
                 population_size,
                 exploit_count,
                 steps_per_exploit,
                 pvc_name,
                 exploiter=Truncation(),
                 explorer=Resample(),
                 ):

        self.hyperparameters = hyperparameters
        self.model_dir = model_dir
        self.population_size = population_size
        #How many instances should be deployed
        self.runs = population_size
        self.exploit_count = exploit_count
        self.steps_per_exploit = steps_per_exploit
        self.pvc_name = pvc_name
        self.exploiter = exploiter  # binary tournament or truncation
        self.explorer = explorer  # perturb or resample
        
        # Values of HP for the latest run
        self.current_hp_values = None
        self.hostname = None
        self.user_func = None
        self.saver = None
        self.redis = None
        self.step_count = 0
        self.curr_exploit_count = 0

    def get_params(self):
      if isinstance(self.hyperparameters, types.FunctionType):
        return self.hyperparameters()
      return self.hyperparameters

    def add_training(self, svc, img, name, volumes, volume_mounts):
        volumes = volumes if volumes else []
        volume_mounts = volume_mounts if volume_mounts else []

        volume_mounts.append({
            "name": "checkpoint",
            "mountPath": os.path.dirname(self.model_dir)
        })
        volumes.append({
            "name": "checkpoint",
            "persistentVolumeClaim": self.pvc_name
        })

        svc, redis_env = self.add_redis(svc, name)
        svc = self.arch.add_jobs(svc, self.runs, img, name, volumes, volume_mounts)
        return svc, [redis_env]

    def add_redis(self, svc, name):
        redis_hostname = '{}-redis'.format(name)
        r_svc = {
            "name": redis_hostname,
            "replicas": 1,
            "containers": [{
                "image": "library/redis",
            }],
            "ports": [{
                'number': 6379,
                'protocol': 'TCP'
            }]
        }
        if not "services" in svc:
            svc["services"] = [r_svc]
        else:
            svc["services"].append(r_svc)
        

        # Metaparticle seem to only support one serving endpoint?
        svc["serve"] = {
            "name": redis_hostname
        }
        # if not 'serve' in svc:
        #     svc["serve"] = r_endpoint
        # else:
        #     svc["serve"].append(r_endpoint)
        return svc, {'name': 'REDIS_HOSTNAME', 'value': redis_hostname}

    # def start_training(self):
    def initialize_training(self):
        self.hostname = os.environ.get('HOSTNAME')
        redis_hostname = os.environ.get('REDIS_HOSTNAME')      
        self.redis = redis.StrictRedis(host=redis_hostname)

    def exec_user_func(self, user_func):
        
        self.user_func = user_func
        self.initialize_training()

        self.graph = tf.Graph()
        self.session = tf.Session(graph=self.graph)
        self.training_loop(self.get_params(), True)

    def training_loop(self, hp, first):
        self.current_hp_values = hp
        self.user_func(self.session, self.graph, first, self.steps_per_exploit, self.reporter, **hp)

    def reporter(self, loss_metric, sess):
        self.step_count += self.steps_per_exploit
        saver = tf.train.Saver()
        saver.save(sess, self.model_dir)
        self.commit_performance_info(loss_metric)
        self.iterate(sess)
    
    def iterate(self, sess):
        if self.curr_exploit_count >= self.exploit_count:
            logger.error("TRAINING FINISHED")
            # Training is finished
            return

        # Exploit
        scoreboard = self.get_scoreboard()
        logger.error("SCOREBOARD")
        logger.error(scoreboard)
        new_model_path, copied_hp = self.exploiter.exploit(self.hostname, scoreboard)
        # session graph model ???Ww
        run_hp = self.current_hp_values
        first = False
        if new_model_path:
            # Explore
            if type(self.explorer) is Resample:
                run_hp = self.get_params()
            else:
                run_hp = self.explorer.explore(copied_hp)

            self.graph = tf.Graph()
            self.session = tf.Session(graph=self.graph)
            saver = tf.train.Saver()
            saver.restore(sess, new_model_path)
            first = True
        self.curr_exploit_count += 1
        self.training_loop(run_hp, first)

    def get_scoreboard(self):
        keys = self.redis.keys()
        scoreboard = []
        for key in keys:
            v = self.redis.get(key).decode('utf8')
            scoreboard.append(json.loads(v))
        return sorted(scoreboard, key=lambda x: x['metric'])
    
    def commit_performance_info(self, metric):
        if type(metric).__module__ == 'numpy':
            metric = metric.item()

        info = {
            "id": self.hostname,
            "metric": metric,
            "step": self.step_count,
            "hp": json.dumps(self.current_hp_values),
            "model_path": self.model_dir,
        }
        self.redis.set(self.hostname, json.dumps(info))
