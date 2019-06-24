from unittest.mock import patch
from fairing.deployers.kfserving.kfserving import KFServing

# Test kfserving function with default_model_uri.
def test_kfserving_default_model_spec():
    kfsvc_name = 'test_kfservice'

    with patch('fairing.deployers.kfserving.kfserving.KFServing.deploy', return_value=kfsvc_name):
        kfsvc = KFServing(framework='tensorflow',
                          default_model_uri='gs://kfserving-samples/models/tensorflow/flowers')
        assert kfsvc.deploy("test") == kfsvc_name

# Test kfserving function with namespace, default_model_uri and canary_model_uri.
def test_kfserving_default_canary_model_spec():
    kfsvc_name = 'test_kfservice'

    with patch('fairing.deployers.kfserving.kfserving.KFServing.deploy', return_value=kfsvc_name):
        kfsvc = KFServing(framework='tensorflow', namespace='kubeflow',
                          default_model_uri='gs://kfserving-samples/models/tensorflow/flowers',
                          canary_model_uri='gs://kfserving-samples/models/tensorflow/flowers')
        assert kfsvc.deploy("test") == kfsvc_name

# Test kfserving function with namespace, default_model_uri, canary_model_uri,
# and canary_traffic_percent
def test_kfserving_canary_traffic_percent():
    kfsvc_name = 'test_kfservice'

    with patch('fairing.deployers.kfserving.kfserving.KFServing.deploy', return_value=kfsvc_name):
        kfsvc = KFServing(framework='tensorflow', namespace='kubeflow',
                          default_model_uri='gs://kfserving-samples/models/tensorflow/flowers',
                          canary_model_uri='gs://kfserving-samples/models/tensorflow/flowers',
                          canary_traffic_percent = 10)
        assert kfsvc.deploy("test") == kfsvc_name

# Test kfserving function with some labels and annotations
def test_kfserving_labels_annotations():
    kfsvc_name = 'test_kfservice'

    with patch('fairing.deployers.kfserving.kfserving.KFServing.deploy', return_value=kfsvc_name):
        kfsvc = KFServing(framework='tensorflow',
                          default_model_uri='gs://kfserving-samples/models/tensorflow/flowers',
                          labels={'test-id': 'test123'},
                          annotations="test=test123")
        assert kfsvc.deploy("test") == kfsvc_name
