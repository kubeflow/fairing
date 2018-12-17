from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import pytest

from fairing.builders import dockerfile

def test_get_base_image(monkeypatch):
    monkeypatch.delenv('FAIRING_DEV', False)
    assert dockerfile.get_default_base_image().startswith("library/python:")

    monkeypatch.setenv('FAIRING_DEV', 1)
    monkeypatch.setenv('FAIRING_DEV_DOCKER_USERNAME', 'wbuchwalter')
    assert dockerfile.get_default_base_image() == "wbuchwalter/fairing:dev"

    monkeypatch.setenv('FAIRING_DEV', 1)
    monkeypatch.delenv('FAIRING_DEV_DOCKER_USERNAME', False)
    # Defining FAIRING_DEV but not FAIRING_DEV_DOCKER_USERNAME
    # should result in an exception
    with pytest.raises(KeyError):
        dockerfile.get_default_base_image()


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

@pytest.mark.parametrize("file_name, expected_name",
                         [
                             ('./test.py', 'test.py'),
                             ('test.py', 'test.py'),
                             ('./here/test.py', 'test.py'),

                         ])
def test_get_exec_file_name(monkeypatch, file_name, expected_name):
    monkeypatch.setattr('sys.argv', [file_name, "--some-arguments"])
    assert dockerfile.get_exec_file_name() == expected_name