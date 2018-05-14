
import logging
import types

# TODO: can we make this framework-agnostic?
import tensorflow as tf

logger = logging.getLogger('metaml')

class ExploitStrategy(object):
    pass


class Truncation(ExploitStrategy):
    pass


class BinaryTournament(ExploitStrategy):
    pass


class ExploreStrategy(object):
    def transform_hp(self, hp_dict):
      raise NotImplementedError()


class Perturb(ExploreStrategy):
    def __init__(self, min_multiplier, max_multiplier):
        self.min_multiplier = min_multiplier,
        self.max_multiplier = max_multiplier
    
    def transform_hp(self, hp_dict):
      raise NotImplementedError


class Resample(ExploreStrategy): pass

class PopulationBasedTraining(object):
    def __init__(self,
                 hyperparameters,
                 #  saver,           # used to restore model
                 model_dir,
                 population_size,
                 exploit_count,
                 steps_per_exploit,
                 exploiter=Truncation(),
                 explorer=Resample(),
                 ):
        self.hyperparameters = hyperparameters

        # Values of HP for the latest run
        self.current_hp_values = None

        self.population_size = population_size
        #How many instances should be deployed
        self.runs = population_size

        self.user_func = None

        self.exploiter = None  # binary tournament or truncation
        self.exploit_count = exploit_count
        self.steps_per_exploit = steps_per_exploit
        self.explorer = None  # perturb or resample

        # Value of the hyperparameters for the current exploration phase
        self.current_hp_val = None

        self.saver = None
        # self.session = None

    def get_params(self):
      if isinstance(self.hyperparameters, types.FunctionType):
        return self.hyperparameters()
      return self.hyperparameters

    # def initialize(self):
    #     self.session = tf.Session()
    #     init_op = tf.global_variables_initializer()
    #     self.session.run(init_op)

    def start_training(self):
      self.user_func(self.steps_per_exploit, self.reporter, **self.current_hp_values)

    def exec_user_func(self, user_func):
        self.user_func = user_func
        # self.initialize()
        self.current_hp_values = self.get_params()

        self.start_training()

        # TODO: PBT core logic goes here
        # 1: create a saver
        # 2: create init op
        # 3: get hyperparameters
        # 4: create a session
        # 5: sess.run(init)
        # 6: call user_func
        # 7: reporter gets called back from user_func


    def reporter(self, performance, saver):
        # 0: Only if self.exploit_step <= self.exploint_count:
        # 1: save session checkpoint
        # 2: communicate with referee to compare performance
        # 3: referee returns path to checkpoint that should be loaded + new set of hp
        # 4: (optional?) perturb/resamble hp
        # 5: self.exec_user_func
        logger.warn('Reported: {}'.format(performance))
        
        

    def explore(self):
        pass

    
