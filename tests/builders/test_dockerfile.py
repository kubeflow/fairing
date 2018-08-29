import pytest

from fairing.builders.dockerfile import DockerFile

@pytest.fixture
def dockerfile():
    return DockerFile()

def test_get_base_image(dockerfile, monkeypatch):
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


# def test_build_dockerfile(dockerfile):
#     steps = [
#         "step 1",
#         "step 2",
#         "step 3"
#     ]
#     cmd = 'some CMD'
#     dockerfile.add_steps(steps)
#     dockerfile.set_cmd(cmd)
#     exp = "FROM library/python:3.6\n" + \
#         '\n'.join(steps) + '\n' + \
#         '{}'.format(cmd)

#     assert exp == dockerfile.build_dockerfile()

def test_get_env_steps(dockerfile):
    env = [
        {'name': 'env1', 'value': 'val1'},
        {'name': 'env2', 'value': 'val2'}
    ]
    exp = [
        "ENV env1 val1",
        "ENV env2 val2"
    ]
    assert exp == dockerfile.get_env_steps(env)

@pytest.mark.parametrize("file_name, expected_name",
                         [
                             ('./test.py', 'test.py'),
                             ('test.py', 'test.py'),
                             ('./here/test.py', 'here/test.py'),

                         ])
def test_get_exec_file_name(dockerfile, monkeypatch, file_name, expected_name):
    monkeypatch.setattr('sys.argv', [file_name, "--some-arguments"])
    assert dockerfile.get_exec_file_name() == expected_name