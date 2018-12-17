import setuptools
import json

setuptools.setup(
    name='fairing',
    version='0.0.3',
    author="William Buchwalter",
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
    setup_requires=[
        'pytest-runner'
    ],
    install_requires=[
        'docker==3.4.1',
        'redis==2.10.6',
        'notebook==5.6.0',
        'jupyter==1.0.0',
        'numpy==1.15.0',
        'kubernetes==8.0.0',
        'future==0.17.1',
        'six==1.11.0',
        'httplib2==0.12.0',
        'oauth2client==4.0.0',
    ],
    tests_require=[
        'mock',
        'pytest',
        'pytest-pep8',
        'pytest-cov',
        'pytest-runner'
    ]
)
