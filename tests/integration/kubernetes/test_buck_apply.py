from kubeflow.fairing.kubernetes.manager import KubeManager

core_api_test = '''
apiVersion: v1
kind: Pod
metadata:
  name: core-api-test
  labels:
    name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
'''

apps_api_test = '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apps-api-test
  labels:
    app: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
'''

custom_resource_test = '''
apiVersion: "kubeflow.org/v1"
kind: "TFJob"
metadata:
  name: "custom-resource-test"
spec:
  tfReplicaSpecs:
    PS:
      replicas: 1
      restartPolicy: Never
      template:
        spec:
          containers:
            - name: tensorflow
              image: kubeflow/tf-dist-mnist-test:1.0
    Worker:
      replicas: 1
      restartPolicy: Never
      template:
        spec:
          containers:
            - name: tensorflow
              image: kubeflow/tf-dist-mnist-test:1.0
'''

kubeflow_client = KubeManager()

def test_apply_namespaced_object_core_v1_api():
    '''
    Test apply_namespaced_object API for CoreV1Api
    '''
    kubeflow_client.apply_namespaced_object(core_api_test)
    kubeflow_client.apply_namespaced_object(core_api_test, mode='patch')
    kubeflow_client.apply_namespaced_object(core_api_test, mode='delete')


def test_apply_namespaced_object_apps_v1_api():
    '''
    Test apply_namespaced_object API for AppV1Api
    '''
    kubeflow_client.apply_namespaced_object(apps_api_test)
    kubeflow_client.apply_namespaced_object(apps_api_test, mode='patch')
    kubeflow_client.apply_namespaced_object(apps_api_test, mode='delete')

def test_apply_namespaced_object_custom_resource_api():
    '''
    Test apply_namespaced_object API for CRD API
    '''
    kubeflow_client.apply_namespaced_object(custom_resource_test)
    kubeflow_client.apply_namespaced_object(custom_resource_test, mode='patch')
    kubeflow_client.apply_namespaced_object(custom_resource_test, mode='delete')

def test_apply_namespaced_objects():
    '''
    Test apply_namespaced_objects for buck applying
    '''
    # To avoid error about the object already exists, rename the resource.
    bulk_resources = [
        core_api_test.replace('core-api-test', 'core-api-test-buck'),
        apps_api_test.replace('apps-api-test', 'apps-api-test-buck'),
        custom_resource_test.replace('custom-resource-test', 'custom-resource-test-buck')
    ]
    kubeflow_client.apply_namespaced_objects(bulk_resources)
    kubeflow_client.apply_namespaced_objects(bulk_resources, mode='patch')
    kubeflow_client.apply_namespaced_objects(bulk_resources, mode='delete')
