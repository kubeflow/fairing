import logging
import uuid

import kubernetes.config

from fairing.builders.dockerfile import DockerFile
from fairing.builders.container_image_builder import ContainerImageBuilder
from fairing.builders.knative.models.build_template import BuildTemplate, BuildTemplateSpec, BuildTemplateSpecParameter, BuildTemplateSpecStep
from fairing.builders.knative.models.build import Build, BuildSpec, BuildSpecArgument, BuildSpecTemplate
from fairing.utils import get_image, is_running_in_k8s, get_current_k8s_namespace

logger = logging.getLogger('fairing')


class KnativeBuilder(ContainerImageBuilder):
    def __init__(self):
        self.dockerfile = DockerFile()
        self.namespace = self.get_current_namespace()
        self._build_id = self.get_unique_id()

    def get_unique_id(self):
        id = uuid.uuid4()
        return str(id).split('-')[0]

    def execute(self, package_options, env):
        image = get_image(package_options)
        self.dockerfile.write(package_options, env)
        self.build_and_push(image)

    def build_and_push(self, img):
        print('Building docker image {}...'.format(img))

        self.authenticate()

        build_template = self.generate_build_template_resource()
        build_template.maybe_create()

        build = self.generate_build_resource(img)
        build.create()

        self.wait_for_build_completion()

        #TODO: clean build?

    def authenticate(self):
        if is_running_in_k8s():
            kubernetes.config.load_incluster_config()
        else:
            kubernetes.config.load_kube_config()

    def get_current_namespace(self):
        if not is_running_in_k8s():
            logger.debug("""Fairing does not seem to be running inside Kubernetes, \
                          cannot infer namespace. Using namespaces 'fairing' instead""")
            return 'fairing'
        return get_current_k8s_namespace()

    def generate_build_template_resource(self):
        metadata = kubernetes.client.V1ObjectMeta(
            name='fairing-build', namespace=self.namespace)

        params = [BuildTemplateSpecParameter(name='IMAGE', description='The name of the image to push'),
                  BuildTemplateSpecParameter(name='TAG', 
                                             description='The tag of the image to push',
                                             default='latest'),
                  BuildTemplateSpecParameter(name='DOCKERFILE',
                                             description='Path to the Dockerfile to build',
                                             default='/src/Dockerfile')]
        volume_mount = kubernetes.client.V1VolumeMount(name='src', mount_path='/src')
        steps = [BuildTemplateSpecStep(name='build-and-push',
                                       image='gcr.io/kaniko-project/executor',
                                       args=['--dockerfile=${DOCKERFILE}',
                                             '--destination=${IMAGE}:${TAG}'],
                                       volume_mounts=[volume_mount])]

        pvc = kubernetes.client.V1PersistentVolumeClaimVolumeSource(
            claim_name='fairing-build')
        volume = kubernetes.client.V1Volume(
            name='src', persistent_volume_claim=pvc)
        spec = BuildTemplateSpec(
            parameters=params, steps=steps, volumes=[volume])
        return BuildTemplate(metadata=metadata, spec=spec)

    def generate_build_resource(self, image):
        metadata = kubernetes.client.V1ObjectMeta(
            name='fairing-build-{}'.format(self._build_id),
            namespace=self.namespace)

        args = [BuildSpecArgument(name='IMAGE', value='docker.io/wbuchwalter/fairing-builds'),
                BuildSpecArgument(name='TAG', value='test'),
                BuildSpecArgument(name='DOCKERFILE', value='/src/Dockerfile')]

        template = BuildSpecTemplate(name='fairing-build', arguments=args)
        spec = BuildSpec(sa_name='fairing-build', template=template)
        return Build(metadata=metadata, spec=spec)

    def wait_for_build_completion(self):
        # Check for build.status.condition.reason
        raise NotImplementedError()

