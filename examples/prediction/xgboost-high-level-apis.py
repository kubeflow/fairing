#!/usr/bin/env python
# coding: utf-8

# # Train and deploy on Kubeflow from Notebooks
#
# This notebook introduces you to using  Fairing to train and deploy a model to Kubernetes Engine. This notebook demonstrate how to:
#
# * Train an XGBoost model in a local notebook,
# * Use  Fairing to train an XGBoost model remotely on Kubernetes using private docker registry,
#
# To learn more about how to run this notebook locally, see the guide to [training and deploying on GCP from a local notebook][gcp-local-notebook].
#
# [gcp-local-notebook]: https://kubeflow.org/docs/fairing/gcp-local-notebook/


# ## Set up your notebook for training an XGBoost model
#
# Import the libraries required to train this model.

# In[ ]:


import argparse
import logging
import joblib
import sys
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor

# In[ ]:


logging.basicConfig(format='%(message)s')
logging.getLogger().setLevel(logging.INFO)


# Define a function to split the input file into training and testing datasets.

# In[ ]:


def read_input(file_name, test_size=0.25):
    """Read input data and split it into train and test."""
    data = pd.read_csv(file_name)
    data.dropna(axis=0, subset=['SalePrice'], inplace=True)

    y = data.SalePrice
    X = data.drop(['SalePrice'], axis=1).select_dtypes(exclude=['object'])

    train_X, test_X, train_y, test_y = train_test_split(X.values,
                                                        y.values,
                                                        test_size=test_size,
                                                        shuffle=False)

    imputer = SimpleImputer()
    train_X = imputer.fit_transform(train_X)
    test_X = imputer.transform(test_X)

    return (train_X, train_y), (test_X, test_y)


# Define functions to train, evaluate, and save the trained model.

# In[ ]:


def train_model(train_X,
                train_y,
                test_X,
                test_y,
                n_estimators,
                learning_rate):
    """Train the model using XGBRegressor."""
    model = XGBRegressor(n_estimators=n_estimators, learning_rate=learning_rate)

    model.fit(train_X,
              train_y,
              early_stopping_rounds=40,
              eval_set=[(test_X, test_y)])

    print("Best RMSE on eval: %.2f with %d rounds" %
          (model.best_score,
           model.best_iteration + 1))
    return model


def eval_model(model, test_X, test_y):
    """Evaluate the model performance."""
    predictions = model.predict(test_X)
    logging.info("mean_absolute_error=%.2f", mean_absolute_error(predictions, test_y))


def save_model(model, model_file):
    """Save XGBoost model for serving."""
    joblib.dump(model, model_file)
    logging.info("Model export success: %s", model_file)


# Define a class for your model, with methods for training and prediction.

# In[ ]:


class HousingServe(object):

    def __init__(self):
        self.train_input = "ames_dataset/train.csv"
        self.n_estimators = 50
        self.learning_rate = 0.1
        self.model_file = "trained_ames_model.dat"
        self.model = None

    def train(self):
        (train_X, train_y), (test_X, test_y) = read_input(self.train_input)
        model = train_model(train_X,
                            train_y,
                            test_X,
                            test_y,
                            self.n_estimators,
                            self.learning_rate)

        eval_model(model, test_X, test_y)
        save_model(model, self.model_file)

    def predict(self, X, feature_names):
        """Predict using the model for given ndarray."""
        if not self.model:
            self.model = joblib.load(self.model_file)
        # Do any preprocessing
        prediction = self.model.predict(data=X)
        # Do any postprocessing
        return [[prediction.item(0), prediction.item(0)]]


# ## Train an XGBoost model in a notebook
#
# Call `HousingServe().train()` to train your model, and then evaluate and save your trained model.

# In[ ]:


HousingServe().train()


import os
import fairing

# You can use any docker container registry istead of docker
DOCKER_REGISTRY = "shikhabitgrit"
PY_VERSION = ".".join([str(x) for x in sys.version_info[0:3]])
BASE_IMAGE = 'python:{}'.format(PY_VERSION)



from fairing import TrainJob
from fairing.backends import KubeflowGKEBackend, KubernetesBackend, GKEBackend

train_job = TrainJob(HousingServe, BASE_IMAGE, input_files=['ames_dataset/train.csv', "requirements.txt"],
                     docker_registry=DOCKER_REGISTRY, backend=KubernetesBackend(),
                     pod_spec_mutators=[fairing.cloud.docker.add_docker_credentials_if_exists])
train_job.submit()

