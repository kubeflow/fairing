

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