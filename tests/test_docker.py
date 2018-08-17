import pytest

from fairing.docker import get_exec_file_name, DockerBuilder
from fairing.utils import is_runtime_phase

@pytest.fixture
def docker_builder():
    return DockerBuilder()

@pytest.mark.parametrize("file_name, expected_name",
                         [
                             ('./test.py', 'test.py'),
                             ('test.py', 'test.py'),
                             ('./here/test.py', 'here/test.py'),

                         ])
def test_get_exec_file_name(monkeypatch, file_name, expected_name):
    monkeypatch.setattr('sys.argv', [file_name, "--some-arguments"])
    assert get_exec_file_name() == expected_name


def test_generate_dockerfile_content(docker_builder, monkeypatch):
    # Monkeypatch execfile
    monkeypatch.setattr('sys.argv', ['/test/bin'])

    env = [{'name': 'TEST_ENV', 'value': 'test_val1'},
           {'name': 'TEST_ENV2', 'value': 'test_val2'}]
    exp = ("FROM library/python:3.6\n"
           "ENV FAIRING_RUNTIME 1\n"
           "COPY ./ /app/\n"
           "RUN pip install --no-cache -r /app/requirements.txt\n"
           "ENV TEST_ENV test_val1\n"
           "ENV TEST_ENV2 test_val2\n"
           "CMD python /app/test/bin")
    c = docker_builder.generate_dockerfile_content(env)
    assert exp == c


def test_generate_dockerfile_content_notebook(docker_builder, monkeypatch):
    # Simulate Notebook environment
    monkeypatch.setattr('fairing.docker.is_in_notebook', lambda: True)
    monkeypatch.setattr('fairing.docker.get_notebook_name', lambda: 'test-notebook')


    env = [{'name': 'TEST_ENV', 'value': 'test_val1'},
           {'name': 'TEST_ENV2', 'value': 'test_val2'}]
    exp = ("FROM library/python:3.6\n"
           "ENV FAIRING_RUNTIME 1\n"
           "COPY ./ /app/\n"
           "RUN pip install --no-cache -r /app/requirements.txt\n"
           "RUN pip install jupyter nbconvert\n"
           "RUN jupyter nbconvert --to script /app/test-notebook\n"
           "ENV TEST_ENV test_val1\n"
           "ENV TEST_ENV2 test_val2\n"
           "CMD python /app/test-notebook")
    c = docker_builder.generate_dockerfile_content(env)
    assert exp == c

def test_get_base_image(docker_builder, monkeypatch):
    assert docker_builder.get_base_image().startswith("library/python:")

def test_get_base_image_dev(docker_builder, monkeypatch):
    monkeypatch.setenv('FAIRING_DEV', 1)
    monkeypatch.setenv('FAIRING_DEV_DOCKER_USERNAME', 'wbuchwalter')
    assert docker_builder.get_base_image() == "wbuchwalter/fairing:latest"

def test_get_base_image_dev_raise_error(docker_builder, monkeypatch):
    monkeypatch.setenv('FAIRING_DEV', 1)
    monkeypatch.delenv('FAIRING_DEV_DOCKER_USERNAME', False)
    # Defining FAIRING_DEV but not FAIRING_DEV_DOCKER_USERNAME
    # should result in an exception
    with pytest.raises(KeyError):
        docker_builder.get_base_image()

def test_process_stream(docker_builder):
    # TODO
    pass
