import setuptools
import json

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='fairing',
    version='0.0.3',
    author="William Buchwalter,Matt Rickard",
    description="Easily train ML models on Kubernetes, directly from your python code.",
    url="https://github.com/kubeflow/fairing",
    packages=setuptools.find_packages(),
    package_data={},
    include_package_data=False,
    zip_safe=False,
    classifiers=(
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'docker==3.4.1',
        'notebook==5.6.0',
        'numpy==1.15.0',
        'kubernetes==8.0.1',
        'future==0.17.1',
        'six==1.11.0',
        'google-cloud-storage==1.13.2',
        'requests==2.21.0',
        'setuptools>=34.0.0',
        'tornado==5.1.1',
        'google-auth==1.6.2',
        'httplib2==0.12.0',
        'oauth2client==4.0.0',
        'prompt-toolkit==1.0.15'
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov'
        ]
    }
)
