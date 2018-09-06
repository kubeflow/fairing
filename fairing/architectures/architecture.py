
class TrainingArchitecture(object):
    def add_jobs(self, svc, count, repository, image_name, image_tag, volumes, volume_mounts):
        raise NotImplementedError()
    
    def get_associated_backend(self):
        raise NotImplementedError()
