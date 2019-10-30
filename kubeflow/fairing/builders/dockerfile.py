import logging
import tempfile

from kubeflow.fairing.constants import constants

logger = logging.getLogger('fairing')

# TODO(@karthikv2k): Need to be refractored into a better template
def write_dockerfile(
        docker_command=None,
        destination=None,
        path_prefix=constants.DEFAULT_DEST_PREFIX,
        base_image=None,
        install_reqs_before_copy=False):
    """Generate dockerfile accoding to the parameters

    :param docker_command: string, CMD of the dockerfile (Default value = None)
    :param destination: string, destination folder for this dockerfile (Default value = None)
    :param path_prefix: string, WORKDIR (Default value = constants.DEFAULT_DEST_PREFIX)
    :param base_image: string, base image, example: gcr.io/kubeflow-image
    :param install_reqs_before_copy: whether to install the prerequisites (Default value = False)

    """
    if not destination:
        _, destination = tempfile.mkstemp(prefix="/tmp/fairing_dockerfile_")
    content_lines = ["FROM {}".format(base_image),
                     "WORKDIR {PATH_PREFIX}".format(PATH_PREFIX=path_prefix),
                     "ENV FAIRING_RUNTIME 1"]
    copy_context = "COPY {} {}".format(path_prefix, path_prefix)
    if install_reqs_before_copy:
        content_lines.append("COPY {}/requirements.txt {}".format(path_prefix, path_prefix))
    content_lines.append("RUN if [ -e requirements.txt ];" +
                         "then pip install --no-cache -r requirements.txt; fi")
    content_lines.append(copy_context)

    if docker_command:
        content_lines.append("CMD {}".format(" ".join(docker_command)))

    content = "\n".join(content_lines)
    with open(destination, 'w') as f:
        f.write(content)
    return destination
