from kubeflow.fairing.preprocessors.base import BasePreProcessor


def test_checking_reqs_file_found_use_case_with_input_files():
    input_files = ["foo", "bar", "/foo/bar", "requirements.txt"]
    preprocessor = BasePreProcessor(input_files=input_files)
    assert preprocessor.is_requirements_txt_file_present()


def test_checking_reqs_file_found_use_case_with_output_map():
    output_map = {
        "foo": "/app/bar",
        "/foo/bar": "/app/requirements.txt"
    }
    preprocessor = BasePreProcessor(output_map=output_map)
    assert preprocessor.is_requirements_txt_file_present()


def test_checking_reqs_file_not_found_use_case_with_input_files():
    input_files = ["foo", "bar", "/foo/bar", "/foo/requirements.txt"]
    preprocessor = BasePreProcessor(input_files=input_files)
    assert not preprocessor.is_requirements_txt_file_present()


def test_checking_reqs_file_not_found_use_case_with_output_map():
    output_map = {
        "foo": "/app/bar",
        "/foo/bar": "/app/foo/requirements.txt"
    }
    preprocessor = BasePreProcessor(output_map=output_map)
    assert not preprocessor.is_requirements_txt_file_present()
