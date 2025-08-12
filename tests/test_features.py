import os
import re
import subprocess
import sys
import sysconfig
from itertools import product
from textwrap import dedent

import pytest

from runtime_introspect._features import CPythonFeatureSet, Feature
from runtime_introspect._status import Status


def test_feature_repr():
    ft = Feature(name="test", status=Status(available=True, enabled=None, active=None))
    assert (
        repr(ft)
        == "Feature(name='test', status=Status(available=True, enabled=None, active=None, details=None))"
    )


def test_feature_immutability():
    ft = Feature(name="test", status=Status(available=True, enabled=None, active=None))
    with pytest.raises(Exception, match="^cannot assign"):
        ft.name = "new-name"
    with pytest.raises(Exception, match="^cannot assign"):
        ft.status = Status(available=None, enabled=None, active=None)
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


ENV_status = [None, "0", "1"]
GIL_JIT_ENV_status = list(product(ENV_status, ENV_status))


@pytest.fixture(
    params=GIL_JIT_ENV_status,
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
        features = fs.snapshot(jit_introspection=jit_introspection)
        assert [ft.name for ft in features] == ["free-threading", "JIT"]

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
                possible_ff_status = {"disabled"}
            else:
                assert GIL is None
                possible_ff_status = {"available", "enabled", "disabled"}
        else:
            possible_ff_status = {"unavailable"}

        ft = res[0]
        assert ft.name == "free-threading"
        assert ft.status.summary in possible_ff_status

        if sys.version_info[:2] == (3, 13):
            possible_jit_status = {"undetermined"}
        elif sys._jit.is_available():
            if jit_introspection == "deep":
                possible_jit_status = {"active", "inactive", "disabled"}
            elif jit_introspection == "stable":
                if JIT == "1":
                    possible_jit_status = {"enabled"}
                else:
                    assert JIT in ("0", None)
                    possible_jit_status = {"disabled"}
            else:  # pragma: no cover
                raise RuntimeError
        else:
            possible_jit_status = {"unavailable"}

        ft = res[1]
        assert ft.name == "JIT"
        assert ft.status.summary in possible_jit_status

    @pytest.mark.parametrize("jit_introspection", ["stable", "deep"])
    def test_featureset_diagnostics(self, jit_introspection):
        fs = CPythonFeatureSet()
        di = fs.diagnostics(jit_introspection=jit_introspection)
        assert len(di) == 2

        possible_status = [r"((un)?available)", r"((en|dis)abled)"]
        extra_possibilities: list[str] = []
        if sys.version_info < (3, 14):
            extra_possibilities.append(r"(undetermined)")
        else:
            if jit_introspection == "deep":
                extra_possibilities.append(r"((in)?active)")
        expected_jit = re.compile(r"|".join(possible_status + extra_possibilities))
        assert expected_jit.search(di[1]) is not None

    def test_invalid_jit_introspection(self):
        fs = CPythonFeatureSet()
        introspection = "invalid"
        expected_msg = (
            rf"^Invalid argument {introspection=!r}\. "
            r"Expected either 'stable' or 'deep'$"
        )
        with pytest.raises(ValueError, match=expected_msg):
            fs.jit(introspection=introspection)

        with pytest.raises(ValueError, match=expected_msg):
            fs.snapshot(jit_introspection=introspection)

        with pytest.raises(ValueError, match=expected_msg):
            fs.diagnostics(jit_introspection=introspection)
