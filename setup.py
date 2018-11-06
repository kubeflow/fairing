import setuptools
import json

setuptools.setup(
    name='fairing',
    version='0.0.3',
    author="William Buchwalter",
    description="Easily train and serve ML models on Kubernetes, directly from your python code.",
    url="https://github.com/wbuchwalter/fairing",
    packages=setuptools.find_packages(),
    package_data={},
    include_package_data=False,
    zip_safe=False,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'docker==3.4.1',
        'redis==2.10.6',
        'notebook==5.6.0',
        'jupyter==1.0.0',
        'numpy==1.15.0',
        'kubernetes==6.0.0'
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov'
        ]
    }
)
