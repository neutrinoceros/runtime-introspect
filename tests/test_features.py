import sys

import pytest

from runtime_features_introspection._features import CPythonFeatureSet, Feature
from runtime_features_introspection._status import (
    Active,
    Available,
    Disabled,
    Enabled,
    Inactive,
    Unavailable,
    Unknown,
)


def test_feature_repr():
    ft = Feature(name="test", status=Available())
    assert repr(ft) == "Feature(name='test', status=Available())"


@pytest.mark.parametrize(
    "status, expected_str",
    [
        pytest.param(Available(), "available", id="available"),
        pytest.param(
            Unavailable(reason="don't have it"),
            "unavailable (don't have it)",
            id="unavailable",
        ),
        pytest.param(Active(), "active", id="active"),
        pytest.param(Inactive(), "inactive", id="inactive"),
        pytest.param(
            Unknown(reason="no idea why"), "unknown (no idea why)", id="unknown"
        ),
        pytest.param(
            Enabled(detail="and too late to stop it now"),
            "enabled, and too late to stop it now",
            id="enabled",
        ),
        pytest.param(
            Disabled(reason="this one is grounded"),
            "disabled (this one is grounded)",
            id="disabled",
        ),
    ],
)
def test_feature_diagnostic(status, expected_str):
    ft = Feature(name="test", status=status)
    assert ft.diagnostic == f"test: {expected_str}"


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
    sys.implementation.name != "cpython", reason="intended as CPython-only"
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
