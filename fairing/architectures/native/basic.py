from fairing.architectures.architecture import TrainingArchitecture
from fairing.backend.native import NativeBackend


class BasicArchitecture(TrainingArchitecture):
    pass

    def add_jobs(self, svc, count, img, name, volumes, volume_mounts):
        svc['jobs'] = [{
            "name": name,
            # TODO should parallelism and completion be surfaced ? How would that be implemented in all backends
            "parallelism": count,
            "completion": count,
            "containers": [
                {
                    "image": img,
                    "volumeMounts": volume_mounts
                }
            ],
            "volumes": volumes
        }]
        return svc

    def get_associated_backend(self):
        return NativeBackend()
