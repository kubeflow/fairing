import pytest
from unittest.mock import Mock, patch

from fairing.train import Trainer, Train
from fairing.backend import NativeBackend
from fairing.strategies.basic import BasicTrainingStrategy
from fairing.builders.container_image_builder import ContainerImageBuilder
from fairing.metaparticle import MetaparticleClient
from fairing.utils import get_image
from fairing.options import PackageOptions

REPO_NAME = 'testrepo'
IMAGE_NAME = 'fairing-test'

@pytest.fixture
def package_options():
  return {'name': IMAGE_NAME, 'repository': REPO_NAME, 'publish': True}

@pytest.fixture
def trainer(package_options):
  return Trainer(package=package_options)

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


#Verify default initialization
def test_train_init(monkeypatch, package_options):
  from fairing.architectures.native.basic import BasicArchitecture

  trainer_mock = Mock()
  monkeypatch.setattr('fairing.train.Trainer', trainer_mock)

  Train(package=package_options)
  call_args = trainer_mock.call_args[0]
  
  assert call_args[0] == package_options
  # TensorBoard options
  assert call_args[1] == None
  assert type(call_args[2]) == BasicArchitecture
  assert type(call_args[3]) == BasicTrainingStrategy

def test_compile_ast(trainer, package_options):
  svc, env = trainer.compile_ast()
  assert env == None
  assert len(svc['jobs']) == 1

  job = svc['jobs'][0]

  assert len(job['containers']) == 1
  assert job['containers'][0]['image'] == get_image(PackageOptions(**package_options))

def test_start_training(trainer, package_options,  mock_strategy):
  # Start training should call exec_user_code method from the chosen strategy
  # with the user code as parameter

  # this object will stand in as user code
  fake_user_object = {'fake_prop': 'fake'}

  trainer = Trainer(package=package_options, strategy=mock_strategy)
  trainer.start_training(fake_user_object)

  mock_strategy.exec_user_code.assert_called_with(fake_user_object)

def test_deploy_training(trainer, package_options, mock_builder, monkeypatch, mock_mp_client):
  monkeypatch.setattr('fairing.train.Trainer.get_metaparticle_client', mock_mp_client)  
  monkeypatch.setattr('fairing.train.get_container_builder', lambda x: mock_builder)  

  trainer = Trainer(package=package_options)

  trainer.deploy_training()

  # Deploy should first generate a Dockerfile, build and finally push the image
  mock_builder.execute.assert_called_once()

@pytest.mark.parametrize("is_runtime_phase", [True, False])
def test_train(is_runtime_phase, mock_trainer, package_options, monkeypatch):
  monkeypatch.setattr('fairing.train.Trainer', mock_trainer)
  monkeypatch.setattr('fairing.train.is_runtime_phase', lambda: is_runtime_phase)
  
  mock_inst = mock_trainer()

  @Train(package=package_options)
  class TestModel(object):
    def train(self):
      print('hey')

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