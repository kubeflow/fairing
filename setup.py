import setuptools

with open('requirements.txt') as f:
    REQUIRES = f.read().splitlines()

setuptools.setup(
    name='kubeflow-fairing',
    version='0.7.0',
    author="Kubeflow Authors",
    author_email='hejinchi@cn.ibm.com',
    license="Apache License Version 2.0",
    description="Kubeflow Fairing Python SDK.",
    long_description="Python SDK for Kubeflow Fairing components.",
    url="https://github.com/kubeflow/fairing",
    packages=setuptools.find_packages(
        include=("kubeflow*", "containerregistry*",)),
    package_data={},
    include_package_data=False,
    zip_safe=False,
    classifiers=(
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    install_requires=REQUIRES,
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov'
        ]
    }
)
