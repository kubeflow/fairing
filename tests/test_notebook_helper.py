from fairing import notebook_helper

def test_convert_notebook():
  converted_notebook = notebook_helper.convert_notebook("tests/testdata/magic_command.ipynb")
  assert "get_ipython()" not in converted_notebook
