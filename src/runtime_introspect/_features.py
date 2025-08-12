__all__ = ["CPythonFeatureSet", "Feature"]
import os
import sys
import sysconfig
from dataclasses import dataclass, replace
from typing import Literal, cast

from runtime_introspect._status import Status


@dataclass(frozen=True, slots=True, kw_only=True)
class Feature:
    name: str
    status: Status

    @property
    def diagnostic(self) -> str:
        return f"{self.name}: {self.status}"


@dataclass(frozen=True, slots=True, kw_only=True)
class CPythonFeatureSet:
    def __post_init__(self) -> None:
        if sys.implementation.name != "cpython":
            raise TypeError(
                "CPythonFeatureSet can only be instantiated from a CPython interpreter"
            )

    @staticmethod
    def _get_free_threading_feature() -> Feature:
        st = Status(available=None, enabled=None, active=None)
        ft = Feature(name="free-threading", status=st)

        if sys.version_info < (3, 13):
            st = replace(
                st, available=False, details="only exists in Python 3.13 and newer"
            )
            return replace(ft, status=st)

        assert sys.version_info >= (3, 13)
        Py_GIL_DISABLED = cast(
            Literal[0, 1, None],
            sysconfig.get_config_var("Py_GIL_DISABLED"),
        )
        if Py_GIL_DISABLED == 0:
            st = replace(
                st,
                available=False,
                details="this interpreter was built without free-threading support",
            )
            return replace(ft, status=st)

        st = replace(st, available=True)
        PYTHON_GIL = os.getenv("PYTHON_GIL")
        if sys._is_gil_enabled():  # pyright: ignore[reportPrivateUsage]
            if PYTHON_GIL == "1":
                details = "global locking is forced by envvar PYTHON_GIL=1"
            else:  # pragma: no cover
                details = (
                    "most likely, one or more already loaded "
                    "extension(s) did not declare compatibility"
                )
            st = replace(st, enabled=False, details=details)
            return replace(ft, status=st)

        st = replace(st, enabled=True)
        if PYTHON_GIL == "0":
            details = "forced by envvar PYTHON_GIL=0"
        else:
            details = "no forcing detected"
        st = replace(st, details=details)
        return replace(ft, status=st)

    @staticmethod
    def _get_jit_feature(deep_introspection: bool) -> Feature:
        st = Status(available=None, enabled=None, active=None)
        ft = Feature(name="JIT", status=st)

        if sys.version_info < (3, 13):
            st = replace(
                st,
                available=False,
                details="JIT compilation only exists in Python 3.13 and newer",
            )
            return replace(ft, status=st)
        if sys.version_info[:2] == (3, 13):
            st = replace(st, details="no introspection API known for Python 3.13")
            return replace(ft, status=st)

        assert sys.version_info >= (3, 14)
        sys_jit = sys._jit  # pyright: ignore[reportPrivateUsage]

        if not sys_jit.is_available():
            st = replace(
                st,
                available=False,
                details="this interpreter was built without JIT compilation support",
            )
            return replace(ft, status=st)

        st = replace(st, available=True)
        PYTHON_JIT = os.getenv("PYTHON_JIT")
        if not sys_jit.is_enabled():
            details: str | None
            if PYTHON_JIT == "0":
                details = "forced by envvar PYTHON_JIT=0"
            elif PYTHON_JIT is None:
                details = "envvar PYTHON_JIT is unset"
            else:  # pragma: no cover
                details = None
            st = replace(st, enabled=False, details=details)
            return replace(ft, status=st)

        st = replace(st, enabled=True)
        if deep_introspection:
            st = replace(st, active=sys_jit.is_active())
            return replace(ft, status=st)

        if PYTHON_JIT not in ("0", None):
            st = replace(st, details=f"by envvar {PYTHON_JIT=!s}")
        else:  # pragma: no cover
            pass

        return replace(ft, status=st)

    def snapshot(
        self, *, jit_introspection: Literal["stable", "deep"] = "stable"
    ) -> list[Feature]:
        return [
            self._get_free_threading_feature(),
            self._get_jit_feature(deep_introspection=jit_introspection == "deep"),
        ]

    def diagnostics(
        self, *, jit_introspection: Literal["stable", "deep"] = "stable"
    ) -> list[str]:
        return [
            ft.diagnostic for ft in self.snapshot(jit_introspection=jit_introspection)
        ]
