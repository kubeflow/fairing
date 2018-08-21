from fairing.builders.container_image_builder import ContainerImageBuilder

class KnativeBuilder(ContainerImageBuilder):
    def execute(self, package_options, env):
        raise NotImplementedError()