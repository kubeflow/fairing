import setuptools
import json

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='fairing',
    version='0.5.3',
    author="Kubeflow Authors",
    description="Python SDK for building, training, and deploying ML models",
    url="https://github.com/kubeflow/fairing",
    packages=setuptools.find_packages(include=("fairing*", "containerregistry*",)),
    package_data={},
    include_package_data=False,
    zip_safe=False,
    classifiers=(
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov'
        ]
    }
)
