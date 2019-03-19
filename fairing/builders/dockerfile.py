from fairing.constants import constants
import logging
logger = logging.getLogger('fairing')

# TODO(@karthikv2k): Need to be refractored into a better template
def write_dockerfile(
        docker_command=None,
        destination=constants.DEFAULT_GENERATED_DOCKERFILE_FILENAME,
        path_prefix=constants.DEFAULT_DEST_PREFIX,
        dockerfile_path=None,
        base_image=None):
    content_lines = [ "FROM {}".format(base_image),
        "WORKDIR {PATH_PREFIX}".format(PATH_PREFIX=path_prefix),
        "ENV FAIRING_RUNTIME 1",
        "COPY {PATH_PREFIX} {PATH_PREFIX}".format(PATH_PREFIX=path_prefix),
        "RUN if [ -e requirements.txt ];" +
        "then pip install --no-cache -r requirements.txt; fi"]
    
    if docker_command:
        content_lines.append("CMD {}".format(" ".join(docker_command)))
    
    content = "\n".join(content_lines)
    with open(destination, 'w') as f:
        f.write(content)
    return destination
