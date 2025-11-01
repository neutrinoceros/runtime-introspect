import sys
import sysconfig

import pytest

from runtime_introspect import runtime_feature_set
from runtime_introspect._features import CPythonFeatureSet, DummyFeatureSet

from .helpers import cpython_only


def test_feature_set_function():
    fs = runtime_feature_set()
    match sys.implementation.name:
        case "cpython":
            cls = CPythonFeatureSet
        case _:
            cls = DummyFeatureSet
    assert type(fs) is cls


def test_feature_set_supports_invalid():
    fs = runtime_feature_set()
    assert fs.supports("invalid-feature-name") is False


@cpython_only
@pytest.mark.skipif(
    sys.version_info >= (3, 15),
    reason="py-limited-api support in 3.15 is not settled yet",
)
@pytest.mark.skipif(
    sys.version_info >= (3, 13) and sysconfig.get_config_var("Py_GIL_DISABLED"),
    reason="different results expected",
)
def test_feature_set_supports_py_limited_api_gil_build():
    fs = runtime_feature_set()
    assert fs.supports("py-limited-api") is True


@cpython_only
@pytest.mark.skipif(
    sys.version_info >= (3, 15),
    reason="py-limited-api support in 3.15 is not settled yet",
)
@pytest.mark.skipif(
    sys.version_info < (3, 13) or sysconfig.get_config_var("Py_GIL_DISABLED") != 1,
    reason="different results expected",
)
def test_feature_set_supports_py_limited_api_ff_build():
    fs = runtime_feature_set()
    assert fs.supports("py-limited-api") is False
