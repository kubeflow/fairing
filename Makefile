.PHONY: dev push_image

dev:
	@if [ -z "${FAIRING_DEV_DOCKER_USERNAME}" ]; then\
		echo "FAIRING_DEV_DOCKER_USERNAME is unset. Set it to your docker username to use this command"; \
	else \
		pip install . ;\
		docker build -t ${FAIRING_DEV_DOCKER_USERNAME}/fairing:latest -f Dockerfile.dev . ; \
	fi

push_image:
	@if [ -z "${FAIRING_DEV_DOCKER_USERNAME}" ]; then\
		echo "FAIRING_DEV_DOCKER_USERNAME is unset. Set it to your docker username to use this command"; \
	else \
		docker push ${FAIRING_DEV_DOCKER_USERNAME}/fairing:latest;\
	fi

push: dev push_image

test: 
	pytest -v
