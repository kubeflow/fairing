.PHONY: dev push_image

# Detect python version from running environment
# This will be used as base image when building the dev version
PY_VERSION := $(shell python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

# List any changed  files. We only include files in the notebooks directory.
# because that is the code in the docker image.
# In particular we exclude changes to the ksonnet configs.
CHANGED_FILES := $(shell git diff-files)

ifeq ($(strip $(CHANGED_FILES)),)
# Changed files is empty; not dirty
# Don't include --dirty because it could be dirty if files outside the ones we care
# about changed.
GIT_VERSION := $(shell git log --pretty=format:'%h' -n 1)
else
GIT_VERSION := $(shell git log --pretty=format:'%h' -n 1)-dirty-$(shell git diff | shasum -a256 | cut -c -6)
endif

TAG := $(shell date +v%Y%m%d)-$(GIT_VERSION)

ifeq ($(strip $(CHANGED_FILES)),)
# Changed files is empty; not dirty
# Don't include --dirty because it could be dirty if files outside the ones we care
# about changed.
GIT_VERSION := $(shell git log --pretty=format:'%h' -n 1)
else
GIT_VERSION := $(shell git log --pretty=format:'%h' -n 1)-dirty-$(shell git diff | shasum -a256 | cut -c -6)
endif

dev:
	@if [ -z "${FAIRING_DEV_DOCKER_USERNAME}" ]; then\
		echo "FAIRING_DEV_DOCKER_USERNAME is unset. Set it to your docker username to use this command"; \
	else \
		pip install . ;\
		docker build --build-arg BASE_IMAGE=library/python:$(PY_VERSION) -t ${FAIRING_DEV_DOCKER_USERNAME}/fairing:dev -f Dockerfile.dev . ; \
	fi

push_image:
	@if [ -z "${FAIRING_DEV_DOCKER_USERNAME}" ]; then\
		echo "FAIRING_DEV_DOCKER_USERNAME is unset. Set it to your docker username to use this command"; \
	else \
		docker push ${FAIRING_DEV_DOCKER_USERNAME}/fairing:dev;\
	fi

push: dev push_image

# Buil a Kubeflow jupyter image
IMG=gcr.io/kubeflow-examples/fairing/jupyter-cpu
build-kubeflow:
	docker build -f "./Dockerfile.kubeflow.jupyter" \
             -t $(IMG):$(TAG) \
             --label=git-versions=$(GIT_VERSION) \
             ./
	@echo Built $(IMG):$(TAG)

push-kubeflow: build-kubeflow
	gcloud docker --authorize-only
	docker push $(IMG):$(TAG)
	@echo Pushed $(IMG):$(TAG)

test: 
	pip install .
	pytest -v
