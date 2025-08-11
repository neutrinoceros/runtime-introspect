import re
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


@not_cpython
def test_featureset_init():
    with pytest.raises(
        TypeError,
        match="^CPythonFeatureSet can only be instantiated from a CPython interpreter$",
    ):
        CPythonFeatureSet()


@cpython_only
class TestCPythonFeatureSet:
    def test_featureset_immutability(self):
        fs = CPythonFeatureSet()
        with pytest.raises(TypeError):
            # not using an exact match because the error message from slots=True is actually
            # not that helpful, as of CPython 3.13.6
            fs.unknown_attr = 123

    @pytest.mark.parametrize("jit_introspection", ["stable", "deep"])
    def test_featureset_snapshot(self, jit_introspection):
        fs = CPythonFeatureSet()
        ss = fs.snapshot(jit_introspection=jit_introspection)
        assert len(ss) == 2
        assert tuple(ss.keys()) == ("free-threading", "JIT")

    @pytest.mark.parametrize("jit_introspection", ["stable", "deep"])
    def test_featureset_diagnostics(self, jit_introspection):
        fs = CPythonFeatureSet()
        di = fs.diagnostics(jit_introspection=jit_introspection)
        assert len(di) == 2

        possible_values = [r"((un)?available)", r"(disabled)"]
        extra_possibilities: list[str] = []
        if sys.version_info < (3, 14):
            extra_possibilities.append(r"(unknown)")
        else:
            if jit_introspection == "deep":
                extra_possibilities.append(r"((in)?active)")
        expected_jit = re.compile(r"|".join(possible_values + extra_possibilities))
        assert expected_jit.search(di[1]) is not None
