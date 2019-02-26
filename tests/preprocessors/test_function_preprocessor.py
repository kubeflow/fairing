import cloudpickle
import pytest
import tarfile

from fairing.preprocessors.function import FunctionPreProcessor

def test_simple_function():
    def foo():
        return "bar"
    fnp = FunctionPreProcessor(foo)
    context_file, _ = fnp.context_tar_gz()
    tar = tarfile.open(context_file)
    fn_file = tar.extractfile(tar.getmember("app/pickled_fn.p"))
    fn = cloudpickle.load(fn_file)
    assert fn() == "bar"
