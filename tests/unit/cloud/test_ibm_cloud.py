from unittest.mock import patch
from kubeflow.fairing.builders.cluster.cos_context import COSContextSource

NAMESPACE = 'default'

def test_ibm_cloud_builder(namespace=NAMESPACE):
    '''
    Test IBM Cloud Builder.
    '''
    mock_result = 'Done'

    with patch('kubeflow.fairing.builders.cluster.cos_context.COSContextSource.upload_context',
               return_value=mock_result):

        aws_key = ('aaaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbb')
        with patch('kubeflow.fairing.cloud.ibm_cloud.get_ibm_cos_credentials',
                   return_value=aws_key):
            cos_context = COSContextSource(namespace=namespace)

        assert cos_context.upload_context('test') == mock_result
