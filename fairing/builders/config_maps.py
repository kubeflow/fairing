import os
import subprocess
import tempfile
import shutil

from kubernetes import client

from fairing import notebook_helper
from .builder import BuilderInterface
from fairing.backend import kubernetes


class ConfigMapBuilder(BuilderInterface):

    def __init__(self, base_image, notebook_name=None):
        if notebook_name is None:
            self.notebook_name = notebook_helper.get_notebook_name()
        else:
            self.notebook_name = notebook_name
        self.base_image = base_image

    def execute(self, namespace, job_id):
        nb_full_path = os.path.join(os.getcwd(), self.notebook_name)

        temp_dir = tempfile.mkdtemp()
        code_path = os.path.join(temp_dir, 'code.py')

        try:
            cmd = "jupyter nbconvert --to python {nb_path} --output {output}"
            .format(
                nb_path=nb_full_path,
                output=code_path
            ).split()

            subprocess.check_call(cmd)
            with open(code_path, 'rb') as f:
                code = f.read()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        client.V1ConfigMap(
            api_version="v1",
            data={"code.py": code},
            metadata=client.V1ObjectMeta(name=self.job_id)
        )
        k8s = kubernetes.KubeManager()
        k8s.create_config_map(namespace, config_map)

    def generate_pod_spec(self, job_id):
        volume_name = 'code'
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=self.base_image,
                command="python /code/code.py".split(),
                volume_mounts=[client.V1VolumeMount(name=volume_name, mount_path='/code')]
            )],
            restart_policy='Never',
            volumes=client.V1Volume(
                name=volume_name,
                config_map=client.V1ConfigMapVolumeSource(name=job_id)
            )
        )
