import setuptools
import json

setuptools.setup(
    name='metaml',
    version='0.1',
    packages=setuptools.find_packages(),
    package_data={},
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        'docker==2.7.0',
        'redis==2.10.6'
    ]
)
