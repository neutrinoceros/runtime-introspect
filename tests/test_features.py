import os
import re
import subprocess
import sys
import sysconfig
from itertools import product
from textwrap import dedent

import pytest

from runtime_introspect._features import CPythonFeatureSet, Feature
from runtime_introspect._status import (
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
        pytest.param(Enabled(detail=None), "enabled", id="enabled-wo-detail"),
        pytest.param(
            Enabled(detail="and too late to stop it now"),
            "enabled, and too late to stop it now",
            id="enabled-w-detail",
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


ENV_VALUES = [None, "0", "1"]
GIL_JIT_ENV_VALUES = list(product(ENV_VALUES, ENV_VALUES))


@pytest.fixture(
    params=GIL_JIT_ENV_VALUES,
    ids=lambda GIL_JIT_tuple: f"GIL={GIL_JIT_tuple[0]}-JIT={GIL_JIT_tuple[1]}",
)
def envvar_setup(request):
    return request.param


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

    @pytest.mark.skipif(
        sys.version_info < (3, 13), reason="envvars are only recognized on Python 3.13+"
    )
    @pytest.mark.parametrize("jit_introspection", ["stable", "deep"])
    def test_featureset_snapshot_w_envvars(
        self, tmp_path, envvar_setup, jit_introspection
    ):
        GIL, JIT = envvar_setup
        script_file = tmp_path / "test_script.py"
        script_file.write_text(
            dedent(f"""
            from pprint import pprint
            from runtime_introspect._features import CPythonFeatureSet

            fs = CPythonFeatureSet()
            ss = fs.snapshot(jit_introspection={jit_introspection!r})
            pprint(ss)
            """)
        )
        env: dict[str, str] = {}
        if GIL is not None:
            env["PYTHON_GIL"] = GIL
        if JIT is not None:
            env["PYTHON_JIT"] = JIT
        if GIL == "0" and sysconfig.get_config_var("Py_GIL_DISABLED") != "1":
            pytest.skip(reason="can't disable the GIL on this build")

        if (COVERAGE_PROCESS_START := os.getenv("COVERAGE_PROCESS_START")) is not None:
            env["COVERAGE_PROCESS_START"] = COVERAGE_PROCESS_START
        else:  # pragma: no cover
            pass

        cp = subprocess.run(
            [sys.executable, str(script_file.resolve())],
            env=env,
            check=True,
            capture_output=True,
        )
        # recreate the snapshot in the parent process...
        # this works because dataclasses' reprs allow for roundtrips, but
        # it's maybe a bit fragile still
        res = eval(cp.stdout.decode())
        if sysconfig.get_config_var("Py_GIL_DISABLED"):
            if GIL == "1":
                possible_ff_types = (Disabled,)
            else:
                assert GIL is None
                possible_ff_types = (Available, Enabled, Disabled)
        else:
            possible_ff_types = (Unavailable,)

        assert isinstance(res["free-threading"], possible_ff_types)

        if sys.version_info[:2] == (3, 13):
            possible_jit_types = (Unknown,)
        elif sys._jit.is_available():
            if jit_introspection == "deep":
                possible_jit_types = (Active, Inactive, Disabled)
            elif jit_introspection == "stable":
                if JIT == "1":
                    possible_jit_types = (Enabled,)
                else:
                    assert JIT in ("0", None)
                    possible_jit_types = (Disabled,)
            else:  # pragma: no cover
                raise RuntimeError
        else:
            possible_jit_types = (Unavailable,)

        assert isinstance(res["JIT"], possible_jit_types)

    @pytest.mark.parametrize("jit_introspection", ["stable", "deep"])
    def test_featureset_diagnostics(self, jit_introspection):
        fs = CPythonFeatureSet()
        di = fs.diagnostics(jit_introspection=jit_introspection)
        assert len(di) == 2

        possible_values = [r"((un)?available)", r"((en|dis)abled)"]
        extra_possibilities: list[str] = []
        if sys.version_info < (3, 14):
            extra_possibilities.append(r"(unknown)")
        else:
            if jit_introspection == "deep":
                extra_possibilities.append(r"((in)?active)")
        expected_jit = re.compile(r"|".join(possible_values + extra_possibilities))
        assert expected_jit.search(di[1]) is not None
