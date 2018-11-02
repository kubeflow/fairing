from abc import ABCMeta, abstractmethod


class ContainerImageBuilder(object):
    __metaclass__ = metacclass=ABCMeta

    @abstractmethod
    def execute(self, repository, image_name, image_tag, base_image, notebook_path, dockerfile_path, publish, env): pass