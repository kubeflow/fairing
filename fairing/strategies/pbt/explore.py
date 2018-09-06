import random
import logging

logger = logging.getLogger('fairing')

class ExploreStrategy(object):
    def explore(self, hp_dict):
      raise NotImplementedError()


class Perturb(ExploreStrategy):
    def __init__(self, min_multiplier=0.8, max_multiplier=1.2):
        self.min_multiplier = min_multiplier
        self.max_multiplier = max_multiplier
    
    def explore(self, hp):  
        new_dict = {}
        for key in hp.keys():
            v = hp[key]

            # Don't touch non decimal HP as they might be batch size, layer size etc...
            # Modifying them will not allow restoring the model
            # TODO: Can we find a better way to do this?
            if type(v) != float:
                new_dict[key] = v
                continue
            perturb_factor = random.uniform(self.min_multiplier, self.max_multiplier)
            new_dict[key] = perturb_factor*v
        return new_dict

class Resample(ExploreStrategy): pass