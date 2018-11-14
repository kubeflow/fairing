from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pytest
from unittest.mock import Mock

from fairing.strategies.basic import BasicTrainingStrategy
from fairing.architectures.native.basic import BasicArchitecture
from fairing.utils import get_image_full

class DummyUserModel(object):
    def train():
        return

    def build():
        pass


@pytest.fixture
def strategy():
    strat = BasicTrainingStrategy()
    strat.set_architecture(BasicArchitecture())
    return strat


@pytest.fixture
def mock_user_object():
    return Mock(spec=DummyUserModel)


def test_exec_user_code(strategy, mock_user_object):
    strategy.exec_user_code(mock_user_object)
    mock_user_object.build.assert_called_once()
    mock_user_object.train.assert_called_once()


def test_add_training(strategy):
    svc = {}
    repo = 'test'
    image_name = 'testimage'
    image_tag = '1.0'
    _, env = strategy.add_training(svc, repo, image_name, image_tag, [], [])
    # there shouldn't be any env variable set by default
    assert env == None

