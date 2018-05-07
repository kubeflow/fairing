# Why?

Easily transfer from jupyter notebook code to containers

@Train(hp_generator=my_hp_generator, draws=1)  -> Sharding from metaparticle for HP Tuning
@DistributedTraining -> Calls in Kubeflow CRD
@DataIn(type='AzureBlob', 'blob://mybucket/some/dataset')
@DataOut(type='AzureBlob')
@TensorBoard(port="5425") -> Does this need to be a decorator? Or an option of Train?
@EarlyStoppingStrategy(func=...)
def training():
...



@Predict(url='/predict', port='80')
