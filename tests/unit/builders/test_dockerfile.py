import pytest
import tempfile

from fairing.builders import dockerfile

def test_writedockerfile_with_docker_cmd():
    _, tmp_file = tempfile.mkstemp()
    dockerfile.write_dockerfile(
                destination=tmp_file,
                docker_command=["python", "main.py"],
                path_prefix="/pre",
                base_image="foo_bar")
    actual = open(tmp_file, 'r').read()
    expected = """FROM foo_bar
WORKDIR /pre
ENV FAIRING_RUNTIME 1
COPY /pre /pre
RUN if [ -e requirements.txt ];then pip install --no-cache -r requirements.txt; fi
CMD python main.py"""
    assert actual == expected

def test_writedockerfile_without_docker_cmd():
    _, tmp_file = tempfile.mkstemp()
    dockerfile.write_dockerfile(
                destination=tmp_file,
                docker_command=None,
                path_prefix="/pre",
                base_image="foo_bar")
    actual = open(tmp_file, 'r').read()
    expected = """FROM foo_bar
WORKDIR /pre
ENV FAIRING_RUNTIME 1
COPY /pre /pre
RUN if [ -e requirements.txt ];then pip install --no-cache -r requirements.txt; fi"""
    assert actual == expected