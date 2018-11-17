from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pytest
from unittest.mock import Mock, patch

from fairing.train import Trainer, Train
from fairing.backend import NativeBackend
from fairing.strategies.basic import BasicTrainingStrategy
from fairing.builders.container_image_builder import ContainerImageBuilder
from fairing.metaparticle import MetaparticleClient
from fairing.utils import get_image_full_name

REPO_NAME = 'testrepo'
IMAGE_NAME = 'fairing-test'
IMAGE_TAG = 'test'


@pytest.fixture
def trainer():
    return Trainer(repository=REPO_NAME, image_name=IMAGE_NAME, image_tag=IMAGE_TAG)


@pytest.fixture
def mock_strategy():
    return Mock(spec=BasicTrainingStrategy)


@pytest.fixture
def mock_mp_client():
    return Mock(spec=MetaparticleClient)


@pytest.fixture
def mock_trainer():
    return Mock(spec=Trainer)


@pytest.fixture
def mock_builder():
    return Mock(spec=ContainerImageBuilder)

def test_compile_ast(trainer):
    trainer.fill_image_name_and_tag()
    svc, env = trainer.compile_ast()
    assert env == None
    assert len(svc['jobs']) == 1

    job = svc['jobs'][0]

    assert len(job['containers']) == 1
    assert job['containers'][0]['image'] == get_image_full_name(REPO_NAME, IMAGE_NAME, IMAGE_TAG)


def test_start_training(mock_strategy):
    # Start training should call exec_user_code method from the chosen strategy
    # with the user code as parameter

    # this object will stand in as user code
    fake_user_object = {'fake_prop': 'fake'}

    trainer = Trainer(repository=REPO_NAME,
                      image_name=IMAGE_NAME,
                      image_tag=IMAGE_TAG,
                      strategy=mock_strategy)

    trainer.start_training(fake_user_object)

    mock_strategy.exec_user_code.assert_called_with(fake_user_object)


def test_deploy_training(mock_builder, mock_mp_client, monkeypatch):
    monkeypatch.setattr(
        'fairing.train.MetaparticleClient', mock_mp_client)
    monkeypatch.setattr(
        'fairing.train.get_container_builder', lambda x: mock_builder)
        
    trainer = Trainer(repository=REPO_NAME)
    trainer.deploy_training(stream_logs=False)

    # Deploy should first generate a Dockerfile, build and finally push the image
    mock_builder.execute.assert_called_once()


@pytest.mark.parametrize("is_runtime_phase", [True, False])
def test_train(is_runtime_phase, mock_trainer, monkeypatch):
    monkeypatch.setattr('fairing.train.Trainer', mock_trainer)
    monkeypatch.setattr('fairing.train.is_runtime_phase',
                        lambda: is_runtime_phase)

    mock_inst = mock_trainer()

    @Train(repository=REPO_NAME)
    class TestModel(object):
        def train(self):
            pass

    model = TestModel()
    model.train()

    # When running outside the metaparticle container (so on a user system),
    # when train() is called, it should build the container and deploy the code into
    # a metaparticle container.
    # Once running in a metaparticle container, train() should instead route to
    # the actual user code (through start_training)
    if is_runtime_phase:
        mock_inst.start_training.assert_called_once()
    else:
        mock_inst.deploy_training.assert_called_once()
