from kubernetes.client.models.v1_resource_requirements import V1ResourceRequirements

def get_resource_mutator(cpu=None, memory=None):
    def _resource_mutator(kube_manager, pod_spec, namespace):
        if cpu is None and memory is None:
            return
        if pod_spec.containers and len(pod_spec.containers)>=1:
            # All cloud providers specify their instace memory in GB
            # so it is peferable for user to specify memory in GB
            # and we convert it to Gi that K8s needs
            limits = {}
            if cpu:
                limits['cpu'] = cpu
            if memory:
                memory_gib =  "{}Gi".format(round(memory/1.073741824, 2))
                limits['memory'] = memory_gib 
            if pod_spec.containers[0].resources:
                if pod_spec.containers[0].resources.limits:
                    pod_spec.containers[0].resources.limits = {}
                for k,v in limits.items():
                    pod_spec.containers[0].resources.limits[k] = v
            else:
                pod_spec.containers[0].resources = V1ResourceRequirements(limits=limits)
    return _resource_mutator
