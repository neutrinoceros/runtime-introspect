import sys

import pytest

cpython_only = pytest.mark.skipif(
    sys.implementation.name != "cpython", reason="intended as CPython-only"
)
not_cpython = pytest.mark.skipif(
    sys.implementation.name == "cpython", reason="behavior differs on CPython"
)
