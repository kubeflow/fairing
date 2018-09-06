from abc import ABCMeta, abstractmethod


class ContainerImageBuilder(object):
    __metaclass__ = metacclass=ABCMeta

    @abstractmethod
    def execute(self, repository, image_name, image_tag, base_image, dockerfile, publish, env): pass