from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from pkg_resources import resource_filename
import shutil
import os
import logging

from kubernetes import client, config

from .models.build import Build, BuildSpec, BuildSpecArgument, BuildSpecTemplate
from .models.build_template import BuildTemplate, BuildTemplateSpec, BuildTemplateSpecParameter, BuildTemplateSpecStep
from fairing.builders import BuilderInterface, dockerfile
from fairing import utils

logger = logging.getLogger(__name__)
DEFAULT_IMAGE_NAME = 'fairing-job'


class KnativeBuilder(BuilderInterface):
    def __init__(self,
                 repository,
                 image_name=DEFAULT_IMAGE_NAME,
                 image_tag=None,
                 dockerfile_path=None):

        self.repository = repository
        self.image_name = image_name
        self.dockerfile_path = dockerfile_path
        self.namespace = self._get_current_namespace()

        if image_tag is None:
            self.image_tag = utils.get_unique_tag()
        else:
            self.image_tag = image_tag
        
        # Unique build_id to avoid conflicts
        self._build_id = utils.get_unique_tag()

    def execute(self, namespace, job_id, base_image):
        dockerfile.write_dockerfile(
            dockerfile_path=self.dockerfile_path,
            base_image=base_image
        )
        self._copy_src_to_mount_point()
        self._build_and_push()
        return self._generate_pod_spec()


    def _generate_pod_spec(self):
        """return a V1PodSpec initialized with the proper container"""
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=utils.get_image_full_name(
                    self.repository, 
                    self.image_name, 
                    self.image_tag
                ),
            )],
            restart_policy='Never'
        )

    def _copy_src_to_mount_point(self):
        context_dir = os.getcwdu()
        dst = os.path.join(self._get_mount_point(), self._build_id)
        shutil.copytree(context_dir, dst)

    def _get_mount_point(self):
        return os.path.join(os.environ['HOME'], '.fairing/build-contexts/')

    def _build_and_push(self):
        logger.warn(
            'Building docker image {repository}/{image}:{tag}...'.format(
                repository=self.repository,
                image=self.image_name,
                tag=self.image_tag
            )
        )
        self._authenticate()

        build_template = self._generate_build_template_resource()
        build_template.maybe_create()

        build = self._generate_build_resource()
        build.create_sync()
        # TODO: clean build?

    def _authenticate(self):
        if utils.is_running_in_k8s():
            config.load_incluster_config()
        else:
            config.load_kube_config()

    def _get_current_namespace(self):
        if not utils.is_running_in_k8s():
            logger.debug("""Fairing does not seem to be running inside  
                Kubernetes, cannot infer namespace. Using namespaces 'fairing'
                instead""")
            return 'fairing'
        return utils.get_current_k8s_namespace()

    def _generate_build_template_resource(self):
        metadata = client.V1ObjectMeta(
            name='fairing-build', namespace=self.namespace)

        params = [BuildTemplateSpecParameter(name='IMAGE', description='The name of the image to push'),
                  BuildTemplateSpecParameter(name='TAG',
                                             description='The tag of the image to push',
                                             default='latest'),
                  BuildTemplateSpecParameter(name='DOCKERFILE',
                                             description='Path to the Dockerfile to build',
                                             default='/src/Dockerfile')]
        volume_mount = client.V1VolumeMount(
            name='src', mount_path='/src')
        steps = [BuildTemplateSpecStep(name='build-and-push',
                                       image='gcr.io/kaniko-project/executor:v0.5.0',
                                       args=['--dockerfile=${DOCKERFILE}',
                                             '--destination=${IMAGE}:${TAG}',
                                             '--context=${CONTEXT}'],
                                       volume_mounts=[volume_mount])]

        pvc = client.V1PersistentVolumeClaimVolumeSource(
            claim_name='fairing-build')
        volume = client.V1Volume(
            name='src', persistent_volume_claim=pvc)
        spec = BuildTemplateSpec(
            parameters=params, steps=steps, volumes=[volume])
        return BuildTemplate(metadata=metadata, spec=spec)

    def _generate_build_resource(self):
        metadata = client.V1ObjectMeta(
            name='fairing-build-{}'.format(self.image_name),
            namespace=self.namespace)

        mount_path = '/src/{build_id}'.format(build_id=self._build_id)

        args = [BuildSpecArgument(name='IMAGE', value=utils.get_image(
                self.repository,
                self.image_name)),
            BuildSpecArgument(name='TAG', value=self.image_tag),
            BuildSpecArgument(name='DOCKERFILE', value=os.path.join(
                mount_path, 'Dockerfile')),
            BuildSpecArgument(name='CONTEXT', value=mount_path)]

        template = BuildSpecTemplate(name='fairing-build', arguments=args)
        spec = BuildSpec(sa_name='fairing-build', template=template)
        return Build(metadata=metadata, spec=spec)
