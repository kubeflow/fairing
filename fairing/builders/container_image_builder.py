from abc import ABCMeta, abstractmethod


class ContainerImageBuilder(object):
    __metaclass__ = metacclass=ABCMeta

    @abstractmethod
    def execute(self, package_options, env): pass