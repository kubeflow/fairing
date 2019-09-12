from unittest.mock import patch
from kubeflow.fairing.deployers.kfserving.kfserving import KFServing
from kubeflow.fairing.constants import constants

DEFAULT_URI = 'gs://kfserving-samples/models/tensorflow/flowers'
CANARY_URI = 'gs://kfserving-samples/models/tensorflow/flowers'


def run_unit_test_kfserving(framework, default_model_uri, **kwargs):
    kfsvc_name = 'test_kfservice'

    with patch('kubeflow.fairing.deployers.kfserving.kfserving.KFServing.deploy',
               return_value=kfsvc_name):
        kfsvc = KFServing(framework=framework,
                          default_model_uri=default_model_uri, **kwargs)
        generated_kfsvc = str(kfsvc.generate_kfservice())
        assert constants.KFSERVING_KIND in generated_kfsvc
        assert constants.KFSERVING_GROUP + '/' + \
            constants.KFSERVING_VERSION in generated_kfsvc
        for key in kwargs:
            if key != "labels":
                assert str(kwargs[key]) in generated_kfsvc
            else:
                assert "test_labels" in generated_kfsvc
        assert kfsvc_name == kfsvc.deploy("test")

# Test kfserving function with default_model_uri.


def test_kfserving_default_model_spec():
    run_unit_test_kfserving('tensorflow', DEFAULT_URI)

# Test kfserving function with namespace, default_model_uri and canary_model_uri.


def test_kfserving_default_canary_model_spec():
    run_unit_test_kfserving('tensorflow', DEFAULT_URI,
                            namespace='kubeflow',
                            canary_model_uri=CANARY_URI)

# Test kfserving function with namespace, default_model_uri, canary_model_uri,
# and canary_traffic_percent


def test_kfserving_canary_traffic_percent():
    run_unit_test_kfserving('tensorflow', DEFAULT_URI,
                            namespace='kubeflow',
                            canary_model_uri=CANARY_URI,
                            canary_traffic_percent=10)

# Test kfserving function with some labels and annotations


def test_kfserving_labels_annotations():
    run_unit_test_kfserving('tensorflow', DEFAULT_URI,
                            namespace='kubeflow',
                            labels={'test-id': 'test_labels'},
                            annotations="test=test123")
