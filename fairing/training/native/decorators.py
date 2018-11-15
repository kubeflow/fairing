from fairing.training import base
from fairing.training import native

class Training(base.TrainingDecoratorInterface):

    def __init__(self, namespace=None):
        self.deployment = native.NativeDeployment(namespace, 1)
    
    def __validate(self, user_object):
        """TODO: Verify that the training conforms to what is expected from 
            a simple training. (probably not HP tuning)
        
        Arguments:
            user_object {[type]} -- [description]
        
        Raises:
            NotImplementedError -- [description]
        """

        raise NotImplementedError()

    def __train(self, user_object):
        self.runtime.execute(user_object)

    def __deploy(self, user_object):
        deployment = native.NativeDeployment()
        deployment.execute()


class HPTuning(base.TrainingDecoratorInterface):

    def __init__(self, namespace=None, runs=1):
        self.deployment = native.NativeDeployment(namespace, runs)
    
    def validate()



