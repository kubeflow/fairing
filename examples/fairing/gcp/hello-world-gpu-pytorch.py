import os
import time


def train():
    time.sleep(300)
    print("Training...")
    import torch
    print(torch.cuda.current_device())
    print(torch.cuda.device(0))
    print(torch.cuda.device_count())
    print(torch.cuda.get_device_name(0))
    time.sleep(1)


if __name__ == '__main__':
    if os.getenv('FAIRING_RUNTIME', None) is not None:
        train()
    else:
        from kubeflow import fairing
        # Setting up google container repositories (GCR) for storing output containers
        # You can use any docker container registry istead of GCR
        GCP_PROJECT = fairing.cloud.gcp.guess_project_name()
        DOCKER_REGISTRY = 'gcr.io/{}/fairing-job'.format(GCP_PROJECT)
        file_name = os.path.basename(__file__)
        print("Executing {} remotely.".format(file_name))
        fairing.config.set_preprocessor('python', executable=file_name)
        fairing.config.set_builder(
            'append', base_image='pytorch/pytorch:1.0-cuda10.0-cudnn7-devel',
            registry=DOCKER_REGISTRY, push=True)
        fairing.config.set_deployer('gcp', scale_tier='BASIC_GPU')
        fairing.config.run()
