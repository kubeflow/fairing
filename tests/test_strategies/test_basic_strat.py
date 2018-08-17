import pytest
from unittest.mock import Mock

from fairing.strategies.basic import BasicTrainingStrategy
from fairing.architectures.native.basic import BasicArchitecture


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
    img_name = 'test/test:1.0'
    name = 'test'
    _, env = strategy.add_training(svc, img_name, name, [], [])
    # there shouldn't be any env variable set by default
    assert env == None

