import pytest
from fairing.options import PackageOptions


def test_package_options_new():
    opt = PackageOptions(repository='test')
    assert opt.repository == 'test'
    assert opt.name == 'fairing-build'
    assert opt.tag

def test_package_options_new_no_tag():
    opt = PackageOptions(repository='test', name='image')
    assert opt.repository == 'test'
    assert opt.name == 'image'
    assert opt.tag == 'latest'