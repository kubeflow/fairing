.PHONY: dev push_image

# Detect python version from running environment
# This will be used as base image when building the dev version
PY_VERSION := $(shell python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

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

test: 
	pip install .
	pytest -v
