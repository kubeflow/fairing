import pytest
import tempfile

from fairing.options import PackageOptions
from fairing.builders.docker import get_exec_file_name, DockerBuilder, DockerFile
from fairing.utils import is_runtime_phase


@pytest.fixture
def docker_builder():
    return DockerBuilder()


@pytest.fixture
def dockerfile():
    return DockerFile()


@pytest.mark.parametrize("file_name, expected_name",
                         [
                             ('./test.py', 'test.py'),
                             ('test.py', 'test.py'),
                             ('./here/test.py', 'here/test.py'),

                         ])
def test_get_exec_file_name(monkeypatch, file_name, expected_name):
    monkeypatch.setattr('sys.argv', [file_name, "--some-arguments"])
    assert get_exec_file_name() == expected_name


def test_dockerfile_get_base_image(dockerfile, monkeypatch):
    assert dockerfile.get_base_image().startswith("library/python:")

    monkeypatch.setenv('FAIRING_DEV', 1)
    monkeypatch.setenv('FAIRING_DEV_DOCKER_USERNAME', 'wbuchwalter')
    assert dockerfile.get_base_image() == "wbuchwalter/fairing:latest"

    monkeypatch.setenv('FAIRING_DEV', 1)
    monkeypatch.delenv('FAIRING_DEV_DOCKER_USERNAME', False)
    # Defining FAIRING_DEV but not FAIRING_DEV_DOCKER_USERNAME
    # should result in an exception
    with pytest.raises(KeyError):
        dockerfile.get_base_image()


def test_dockerfile_add_step(dockerfile):
    dockerfile.add_step('some step')
    dockerfile.add_step('some other step')
    assert len(dockerfile.steps) == 2


def test_dockerfile_add_steps(dockerfile):
    dockerfile.add_steps(['some step', 'some other step', 'some third step'])
    assert len(dockerfile.steps) == 3


def test_dockerfile_build_dockerfile(dockerfile):
    steps = [
        "step 1",
        "step 2",
        "step 3"
    ]
    cmd = 'some CMD'
    dockerfile.add_steps(steps)
    dockerfile.set_cmd(cmd)
    exp = "FROM library/python:3.6\n" + \
        '\n'.join(steps) + '\n' + \
        '{}'.format(cmd)

    assert exp == dockerfile.build_dockerfile()

def test_get_env_steps(docker_builder):
    env = [
        {'name': 'env1', 'value': 'val1'},
        {'name': 'env2', 'value': 'val2'}
    ]
    exp = [
        "ENV env1 val1",
        "ENV env2 val2"
    ]
    assert exp == docker_builder.get_env_steps(env)

# def test_generate_dockerfile_content(docker_builder, monkeypatch):
#     # Monkeypatch execfile
#     monkeypatch.setattr('sys.argv', ['/test/bin'])

#     env = [{'name': 'TEST_ENV', 'value': 'test_val1'},
#            {'name': 'TEST_ENV2', 'value': 'test_val2'}]
#     exp = ("FROM library/python:3.6\n"
#            "ENV FAIRING_RUNTIME 1\n"
#            "RUN pip install fairing\n"
#            "COPY ./ /app/\n"
#            "RUN pip install --no-cache -r /app/requirements.txt\n"
#            "ENV TEST_ENV test_val1\n"
#            "ENV TEST_ENV2 test_val2\n"
#            "CMD python /app/test/bin")
#     c = docker_builder.generate_dockerfile_content(env)
#     assert exp == c


# def test_generate_dockerfile_content_notebook(docker_builder, monkeypatch):
#     # Simulate Notebook environment
#     monkeypatch.setattr('fairing.builders.docker.is_in_notebook', lambda: True)
#     monkeypatch.setattr(
#         'fairing.builders.docker.get_notebook_name', lambda: 'test-notebook')

#     env = [{'name': 'TEST_ENV', 'value': 'test_val1'},
#            {'name': 'TEST_ENV2', 'value': 'test_val2'}]
#     exp = ("FROM library/python:3.6\n"
#            "ENV FAIRING_RUNTIME 1\n"
#            "RUN pip install fairing\n"
#            "COPY ./ /app/\n"
#            "RUN pip install --no-cache -r /app/requirements.txt\n"
#            "RUN pip install jupyter nbconvert\n"
#            "RUN jupyter nbconvert --to script /app/test-notebook\n"
#            "ENV TEST_ENV test_val1\n"
#            "ENV TEST_ENV2 test_val2\n"
#            "CMD python /app/test-notebook")
#     c = docker_builder.generate_dockerfile_content(env)
#     assert exp == c
