import sys

import pytest

from runtime_features_introspection._features import CPythonFeatureSet, Feature
from runtime_features_introspection._status import Available


def test_feature_repr():
    ft = Feature(name="test", status=Available())
    assert repr(ft) == "Feature(name='test', status=Available())"


def test_feature_diagnostic():
    ft = Feature(name="test", status=Available())
    assert ft.diagnostic == "test: available"


def test_feature_immutability():
    ft = Feature(name="test", status=Available())
    with pytest.raises(Exception, match="^cannot assign"):
        ft.name = "new-name"
    with pytest.raises(Exception, match="^cannot assign"):
        ft.status = Available()
    with pytest.raises(TypeError):
        # not using an exact match because the error message from slots=True is actually
        # not that helpful, as of CPython 3.13.6
        ft.unknown_attr = 123


cpython_only = pytest.mark.skipif(
    sys.implementation.name != "cpython", reason="intented as CPython-only"
)
not_cpython = pytest.mark.skipif(
    sys.implementation.name == "cpython", reason="behavior differs on CPython"
)


class TestCPythonFeatureSet:
    @not_cpython
    def test_featureset_init(self):
        with pytest.raises(
            TypeError,
            match="^CPythonFeatureSet can only be instantiated from a CPython interpreter$",
        ):
            CPythonFeatureSet()

    @cpython_only
    def test_featureset_immutability(self):
        fs = CPythonFeatureSet()
        with pytest.raises(TypeError):
            # not using an exact match because the error message from slots=True is actually
            # not that helpful, as of CPython 3.13.6
            fs.unknown_attr = 123

    @cpython_only
    def test_featureset_snapshot(self):
        fs = CPythonFeatureSet()
        ss = fs.snapshot()
        assert isinstance(ss, frozenset)
        assert len(ss) == 2
        assert {ft.name for ft in ss} == {"free-threading", "JIT compilation"}
