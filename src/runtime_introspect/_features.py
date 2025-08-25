__all__ = ["CPythonFeatureSet", "Feature"]
import os
import sys
import sysconfig
from dataclasses import dataclass, replace
from typing import Final, Literal, TypeAlias, cast

from runtime_introspect._status import Status


@dataclass(frozen=True, slots=True, kw_only=True)
class Feature:
    """Represent the state of a feature at instantiation time."""

    name: str
    status: Status

    @property
    def diagnostic(self) -> str:
        """A legible diagnostic."""
        return f"{self.name}: {self.status.summary}"


Introspection: TypeAlias = Literal["stable", "unstable-inspect-activity"]
VALID_INTROSPECTIONS: Final[list[Introspection]] = [
    "stable",
    "unstable-inspect-activity",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class CPythonFeatureSet:
    """Represents optional CPython features.

    This class can only be instantiated by a CPython interpreter.
    If a different implementation is detected, will raise a TypeError.
    """

    def __post_init__(self) -> None:
        if sys.implementation.name != "cpython":
            raise TypeError(
                "CPythonFeatureSet can only be instantiated from a CPython interpreter"
            )

    def _free_threading(self) -> Feature:
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
            if sys._xoptions.get("gil") == "1":  # pyright: ignore[reportPrivateUsage]
                details = "global locking is forced by command line option -Xgil=1"
            elif PYTHON_GIL == "1":
                details = "global locking is forced by envvar PYTHON_GIL=1"
            else:  # pragma: no cover
                details = (
                    "most likely, one or more already loaded "
                    "extension(s) did not declare compatibility"
                )
            st = replace(st, enabled=False, details=details)
            return replace(ft, status=st)

        st = replace(st, enabled=True)
        if sys._xoptions.get("gil") == "0":  # pyright: ignore[reportPrivateUsage]
            details = "forced by command line option -Xgil=0"
        elif PYTHON_GIL == "0":
            details = "forced by envvar PYTHON_GIL=0"
        else:
            details = "no forcing detected"
        st = replace(st, details=details)
        return replace(ft, status=st)

    def _jit(self, *, introspection: Introspection = "stable") -> Feature:
        if introspection not in ("stable", "unstable-inspect-activity"):
            raise ValueError(
                f"Invalid argument {introspection=!r}. "
                f"Expected one of {VALID_INTROSPECTIONS}"
            )
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
        sys_jit = sys._jit  # pyright: ignore

        if not sys_jit.is_available():  # pyright: ignore
            st = replace(
                st,
                available=False,
                details="this interpreter was built without JIT compilation support",
            )
            return replace(ft, status=st)

        st = replace(st, available=True)
        PYTHON_JIT = os.getenv("PYTHON_JIT")
        if not sys_jit.is_enabled():  # pyright: ignore
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
        if introspection == "unstable-inspect-activity":
            jit_is_active: bool = sys_jit.is_active()  # pyright: ignore
            st = replace(st, active=jit_is_active)
            return replace(ft, status=st)

        if PYTHON_JIT not in ("0", None):  # pragma: no branch
            st = replace(st, details=f"by envvar {PYTHON_JIT=!s}")

        return replace(ft, status=st)

    def snapshot(self, *, introspection: Introspection = "stable") -> list[Feature]:
        """
        Create a snapshot of the feature set.

        Returns a list of immutable Feature instances, representing the state
        of the runtime at the time this method is invoked.

        Parameters
        ----------

        introspection: 'stable' (default) or 'unstable-inspect-activity'
          For some features, active and inactive status can only be inspected
          using APIs that might, as a side effect, alter said status.
          Use introspection='unstable-inspect-activity' for more accurate
          reporting if this is acceptable in your application.
        """
        return [
            self._free_threading(),
            self._jit(introspection=introspection),
        ]

    def diagnostics(self, *, introspection: Introspection = "stable") -> list[str]:
        """
        Produce legible diagnostics as a list of strings.

        Parameters
        ----------

        introspection: 'stable' (default) or 'unstable-inspect-activity'
          For some features, active and inactive status can only be inspected
          using APIs that might, as a side effect, alter said status.
          Use introspection='unstable-inspect-activity' for more accurate
          reporting if this is acceptable in your application.
        """
        return [ft.diagnostic for ft in self.snapshot(introspection=introspection)]
