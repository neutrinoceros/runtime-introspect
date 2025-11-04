import os
import re
import subprocess
import sys
import sysconfig
from dataclasses import dataclass
from itertools import chain, combinations, product
from textwrap import dedent
from typing import Literal, TypeAlias

import pytest

from runtime_introspect._features import (
    VALID_FEATURE_NAMES,
    VALID_INTROSPECTIONS,
    CPythonFeatureSet,
    DummyFeatureSet,
    Feature,
)
from runtime_introspect._status import Status

from .helpers import cpython_only, not_cpython


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


@not_cpython
def test_foreign_featureset_init():
    with pytest.raises(
        TypeError,
        match="^CPythonFeatureSet can only be instantiated from a CPython interpreter$",
    ):
        CPythonFeatureSet()


ENV_VAL = ["0", "1", None]
EnvSwitch: TypeAlias = Literal["0", "1", None]


@dataclass(frozen=True, slots=True, kw_only=True)
class Environment:
    GIL: EnvSwitch
    JIT: EnvSwitch


@dataclass(frozen=True, slots=True, kw_only=True)
class Settings:
    environment: Environment
    xoptions: list[str]


ENVIRONMENTS = [Environment(GIL=GIL, JIT=JIT) for GIL, JIT in product(ENV_VAL, ENV_VAL)]
SETTINGS = [
    Settings(environment=env, xoptions=([f"gil={GIL}"] if GIL is not None else []))
    for env in ENVIRONMENTS
    for GIL in ENV_VAL
]


@pytest.fixture(
    params=SETTINGS,
    ids=lambda s: f"GIL={s.environment.GIL}-JIT={s.environment.JIT}-X={s.xoptions}",
)
def settings(request):
    return request.param


@cpython_only
class TestCPythonFeatureSet:
    def test_featureset_immutability(self):
        fs = CPythonFeatureSet()
        with pytest.raises(TypeError):
            # not using an exact match because the error message from slots=True is actually
            # not that helpful, as of CPython 3.13.6
            fs.unknown_attr = 123

    @pytest.mark.parametrize("introspection", VALID_INTROSPECTIONS)
    def test_featureset_snapshot(self, introspection):
        fs = CPythonFeatureSet()
        features = fs.snapshot(introspection=introspection)
        assert [ft.name for ft in features] == [
            "free-threading",
            "JIT",
            "py-limited-api",
        ]

    @pytest.mark.skipif(
        sys.version_info < (3, 13),
        reason="startup options under test are only recognized on Python 3.13+",
    )
    @pytest.mark.parametrize("introspection", VALID_INTROSPECTIONS)
    def test_featureset_snapshot_w_startup_options(
        self, tmp_path, settings, introspection
    ):
        env = settings.environment

        is_gil_forced_disabled = "gil=0" in settings.xoptions or (
            "gil=1" not in settings.xoptions and env.GIL == "0"
        )
        is_gil_forced_enabled = "gil=1" in settings.xoptions or (
            "gil=0" not in settings.xoptions and env.GIL == "1"
        )

        if sysconfig.get_config_var("Py_GIL_DISABLED") != 1 and (
            is_gil_forced_disabled or "gil=1" in settings.xoptions
        ):
            pytest.skip(reason="invalid GIL settings + build combo")

        script_file = tmp_path / "test_script.py"
        script_file.write_text(
            dedent(f"""
            from pprint import pprint
            from runtime_introspect._features import CPythonFeatureSet

            fs = CPythonFeatureSet()
            ss = fs.snapshot(introspection={introspection!r})
            pprint(ss)
            """)
        )

        env_dict: dict[str, str] = {
            "COVERAGE_PROCESS_START": os.getenv(
                "COVERAGE_PROCESS_START",
                default="pyproject.toml",
            )
        }
        if env.GIL is not None:
            env_dict["PYTHON_GIL"] = env.GIL
        if env.JIT is not None:
            env_dict["PYTHON_JIT"] = env.JIT

        xoptions = [f"-X{opt}" for opt in settings.xoptions]
        cp = subprocess.run(
            [sys.executable, *xoptions, str(script_file.resolve())],
            env=env_dict,
            check=True,
            capture_output=True,
        )
        # recreate the snapshot in the parent process...
        # this works because dataclasses' reprs allow for roundtrips, but
        # it's maybe a bit fragile still
        res = eval(cp.stdout.decode())
        expected_details: str | None = None
        if sysconfig.get_config_var("Py_GIL_DISABLED"):
            if is_gil_forced_enabled:
                possible_ff_status = {"disabled"}
                if "gil=1" in settings.xoptions:
                    expected_details = (
                        "global locking is forced by command line option -Xgil=1"
                    )
                elif env.GIL == "1":
                    expected_details = "global locking is forced by envvar PYTHON_GIL=1"
                else:
                    raise RuntimeError
            elif is_gil_forced_disabled:
                possible_ff_status = {"enabled"}
                if "gil=0" in settings.xoptions:
                    expected_details = "forced by command line option -Xgil=0"
                elif env.GIL == "0":
                    expected_details = "forced by envvar PYTHON_GIL=0"
                else:
                    raise RuntimeError
            else:
                possible_ff_status = {"available", "enabled", "disabled"}
        else:
            possible_ff_status = {"unavailable"}

        ft = res[0]
        assert ft.name == "free-threading"
        assert ft.status.label in possible_ff_status
        if expected_details is not None:
            assert ft.status.details == expected_details

        if sys.version_info[:2] == (3, 13):
            possible_jit_status = {"undetermined"}
        elif sys._jit.is_available():
            if introspection == "unstable-inspect-activity":
                possible_jit_status = {"active", "inactive", "disabled"}
            elif introspection == "stable":
                if env.JIT == "1":
                    possible_jit_status = {"enabled"}
                else:
                    assert env.JIT in ("0", None)
                    possible_jit_status = {"disabled"}
            else:
                raise RuntimeError
        else:
            possible_jit_status = {"unavailable"}

        ft = res[1]
        assert ft.name == "JIT"
        assert ft.status.label in possible_jit_status

    @pytest.mark.parametrize(
        "features",
        chain.from_iterable(
            combinations(VALID_FEATURE_NAMES, n)
            for n in range(1, len(VALID_FEATURE_NAMES) + 1)
        ),
    )
    @pytest.mark.parametrize("introspection", VALID_INTROSPECTIONS)
    def test_featureset_diagnostics(self, features, introspection):
        fs = CPythonFeatureSet()
        di = fs.diagnostics(features=features, introspection=introspection)
        assert len(di) == len(features)

        if "JIT" not in features:
            return

        possible_status = [r"((un)?available)", r"((en|dis)abled)"]
        extra_possibilities: list[str] = []
        if sys.version_info < (3, 14):
            extra_possibilities.append(r"(undetermined)")
        else:
            if introspection == "unstable-inspect-activity":
                extra_possibilities.append(r"((in)?active)")
        expected_jit = re.compile(r"|".join(possible_status + extra_possibilities))
        assert expected_jit.search(di[features.index("JIT")]) is not None

    @pytest.mark.parametrize("method_name", ["snapshot", "diagnostics"])
    def test_invalid_introspection(self, method_name):
        fs = CPythonFeatureSet()
        introspection = "invalid"
        method = getattr(fs, method_name)
        with pytest.raises(
            ValueError,
            match=(
                rf"^Invalid argument {introspection=!r}\. "
                rf"Expected one of {re.escape(str(VALID_INTROSPECTIONS))}$"
            ),
        ):
            method(introspection=introspection)


class TestDummyFeatureSet:
    def test_snapshot(self):
        fs = DummyFeatureSet()
        assert fs.snapshot() == []

    def test_diagnostics(self):
        fs = DummyFeatureSet()
        assert fs.diagnostics() == []
