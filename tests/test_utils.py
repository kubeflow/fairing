import pytest

from fairing.utils import is_runtime_phase

@pytest.mark.parametrize("runtime_phase", [True, False])
def test_is_runtime_phase(runtime_phase, monkeypatch):
    if runtime_phase:
        monkeypatch.setenv("FAIRING_RUNTIME", True)
    assert is_runtime_phase() == runtime_phase