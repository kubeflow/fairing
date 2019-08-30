import cloudpickle
import tarfile

from kubeflow.fairing.preprocessors.function import FunctionPreProcessor


def test_simple_function():
    def foo_test():
        return "bar"
    foo_test.__module__ = '__main__'
    fnp = FunctionPreProcessor(foo_test)
    context_file, _ = fnp.context_tar_gz()
    tar = tarfile.open(context_file)
    fn_file = tar.extractfile(tar.getmember("app/pickled_fn.p"))
    fn = cloudpickle.load(fn_file)
    assert fn() == "bar"
