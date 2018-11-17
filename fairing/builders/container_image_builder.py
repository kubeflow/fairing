from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from abc import ABCMeta, abstractmethod


class ContainerImageBuilder(object):
    __metaclass__ = metacclass=ABCMeta

    @abstractmethod
    def execute(self, repository, image_name, image_tag, base_image, dockerfile, publish, env): pass