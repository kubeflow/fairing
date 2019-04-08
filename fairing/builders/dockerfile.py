from fairing.constants import constants
import logging
import tempfile
logger = logging.getLogger('fairing')

# TODO(@karthikv2k): Need to be refractored into a better template
def write_dockerfile(
        docker_command=None,
        destination=None,
        path_prefix=constants.DEFAULT_DEST_PREFIX,
        dockerfile_path=None,
        base_image=None,
        install_reqs_before_copy=False):
    if not destination:
        _, destination = tempfile.mkstemp(prefix="/tmp/fairing_dockerfile_")
    content_lines = [ "FROM {}".format(base_image),
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
