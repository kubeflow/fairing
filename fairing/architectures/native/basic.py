from fairing.architectures.architecture import TrainingArchitecture
from fairing.backend.native import NativeBackend
from fairing.utils import get_image_full

class BasicArchitecture(TrainingArchitecture):

    def add_jobs(self, svc, count, repository, image_name, image_tag, volumes, volume_mounts):
        full_image_name = get_image_full(repository, image_name, image_tag)
        svc['jobs'] = [{
            "name": image_name,
            # TODO should parallelism and completion be surfaced ? How would that be implemented in all backends
            "parallelism": count,
            "completion": count,
            "containers": [
                {
                    "image": full_image_name,
                    "volumeMounts": volume_mounts
                }
            ],
            "volumes": volumes
        }]
        return svc

    def get_associated_backend(self):
        return NativeBackend()
