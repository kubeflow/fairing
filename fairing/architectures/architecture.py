from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

class TrainingArchitecture(object):
    def add_jobs(self, svc, count, repository, image_name, image_tag, volumes, volume_mounts):
        raise NotImplementedError()
    
    def get_associated_backend(self):
        raise NotImplementedError()
