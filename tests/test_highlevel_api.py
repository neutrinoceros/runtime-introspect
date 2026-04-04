import sys

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
    assert fs.supports("invalid-feature-name") is None


@cpython_only
def test_feature_set_supports_free_threading():
    fs = runtime_feature_set()
    assert isinstance(fs.supports("free-threading"), bool)
