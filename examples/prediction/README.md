### Train locally

```
python HousingTrain.py --model-file=trained_ames_model.dat --train-input=ames_dataset/train.csv
```

### Serve on Kubernetes

Set a docker registry that you are authenticated to in the set_builder command.

```
fairing.config.set_builder('docker',
    registry='<YOUR-REGISTRY-HERE>',
    base_image="seldonio/seldon-core-s2i-python3:0.4")
```

Serve the model

```
python HousingServe.py
```

Query the endpoint that is given

```
curl -H "Content-Type: application/x-www-form-urlencoded" -d 'json={"data":{"tensor":{"shape":[1,37],"values":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37]}}}' $PREDICTION_ENDPOINT
```
