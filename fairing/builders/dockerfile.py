from fairing.constants import constants
import logging
logger = logging.getLogger('fairing')


def write_dockerfile(
        destination=constants.DEFAULT_GENERATED_DOCKERFILE_FILENAME,
        path_prefix=constants.DEFAULT_DEST_PREFIX,
        dockerfile_path=None,
        base_image=None):
    content = '\n'.join([
        "FROM {}".format(base_image),
        "WORKDIR {PATH_PREFIX}".format(PATH_PREFIX=path_prefix),
        "ENV FAIRING_RUNTIME 1",
        "COPY {PATH_PREFIX} {PATH_PREFIX}".format(PATH_PREFIX=path_prefix),
        "RUN if [ -e requirements.txt ];" +
        "then pip install --no-cache -r requirements.txt; fi"
    ])
    with open(destination, 'w') as f:
        f.write(content)
    return destination
