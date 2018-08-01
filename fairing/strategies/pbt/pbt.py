
import logging
import types
import redis
import os
import json
import math
import numpy as np
import time

from ..basic import BasicTrainingStrategy
from .exploit import Truncation
from .explore import Resample, Perturb
from fairing.docker import is_in_docker_container

#TODO: can we make this class framework agnostic?
if is_in_docker_container():
    import tensorflow as tf

logger = logging.getLogger('fairing')

class PopulationBasedTraining(BasicTrainingStrategy):
    def __init__(self,
                 model_path,
                 population_size,
                 exploit_count,
                 steps_per_exploit,
                 pvc_name,
                 exploiter=Truncation(),
                 explorer=Perturb(),
                 ):

        self.model_path = model_path
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
        self.redis = None
        self.step_count = 0
        self.curr_exploit_count = 0

    def add_training(self, svc, img, name, volumes, volume_mounts):
        volumes = volumes if volumes else []
        volume_mounts = volume_mounts if volume_mounts else []

        volume_mounts.append({
            "name": "checkpoint",
            "mountPath": os.path.dirname(self.model_path)
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
        

        #Metaparticle seem to only support one serving endpoint?
        svc["serve"] = {
            "name": redis_hostname
        }
        # if not 'serve' in svc:
        #     svc["serve"] = r_endpoint
        # else:
        #     svc["serve"].append(r_endpoint)
        return svc, {'name': 'REDIS_HOSTNAME', 'value': redis_hostname}

    def get_params(self):
        hp = None
        hp_func = getattr(self.user_object, "hyperparameters", None)
        if callable(hp_func):
            hp = hp_func()
        return hp

    def exec_user_code(self, user_object):
        self.user_object = user_object
        self.initialize_training()

        params = self.get_params()
        self.user_object.build(params)
        self.training_loop(params)

    def training_loop(self, hp):
        self.current_hp_values = hp
        self.user_object.train(self.steps_per_exploit, self.reporter, hp)

    def initialize_training(self):
        self.hostname = os.environ.get('HOSTNAME')
        redis_hostname = os.environ.get('REDIS_HOSTNAME')      
        self.redis = redis.StrictRedis(host=redis_hostname)

    def reporter(self, loss_metric):
        self.step_count += self.steps_per_exploit
        self.user_object.save()
        self.commit_performance_info(loss_metric)
        self.iterate()
    
    def iterate(self):
        if self.curr_exploit_count >= self.exploit_count:
            # Training is finished
            return

        # Exploit
        scoreboard = self.get_scoreboard()
        new_model_path, copied_hp = self.exploiter.exploit(self.hostname, scoreboard)
        run_hp = self.current_hp_values

        if new_model_path:
            # Explore
            if type(self.explorer) is Resample:
                run_hp = self.get_params()
            else:
                run_hp = self.explorer.explore(copied_hp)
            self.user_object.build(run_hp)
            self.user_object.restore(new_model_path)

        self.curr_exploit_count += 1
        self.training_loop(run_hp)

    def get_scoreboard(self):
        keys = self.redis.keys()
        while len(keys) < self.population_size:
            logger.error("Population size is {}, but only found {} scores. Will retry in 10 seconds".format(
                self.population_size,
                len(keys)
            ))
            time.sleep(10)
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
            "model_path": self.model_path,
        }
        self.redis.set(self.hostname, json.dumps(info))
