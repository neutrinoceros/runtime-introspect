__all__ = ["CPythonFeatureSet", "Feature"]
import os
import sys
import sysconfig
from dataclasses import dataclass
from typing import Literal

from runtime_features_introspection._status import (
    Active,
    Available,
    Disabled,
    Enabled,
    Inactive,
    Status,
    Unavailable,
    Unknown,
)

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never


@dataclass(frozen=True, slots=True, kw_only=True)
class Feature:
    name: str
    status: Status

    @property
    def diagnostic(self) -> str:
        stat_str: str = self.status.__class__.__name__.lower()
        msg: str
        match self.status:
            case Active() | Inactive() | Available() as st:
                msg = stat_str
            case Enabled() as st:
                msg = f"{stat_str}, {st.detail}"
            case Disabled() | Unavailable() | Unknown() as st:
                msg = f"{stat_str} ({st.reason})"
            case _ as unreachable:  # pragma: no cover
                assert_never(unreachable)
        return f"{self.name}: {msg}"


@dataclass(frozen=True, slots=True, kw_only=True)
class CPythonFeatureSet:
    def __post_init__(self) -> None:
        if sys.implementation.name != "cpython":
            raise TypeError(
                "CPythonFeatureSet can only be instantiated from a CPython interpreter"
            )

    @staticmethod
    def snapshot(
        *, jit_introspection: Literal["stable", "deep"] = "stable"
    ) -> frozenset[Feature]:
        free_threading: Status
        PYTHON_GIL = os.getenv("PYTHON_GIL")
        if sys.version_info < (3, 13):
            free_threading = Unavailable(
                reason="free-threading only exists in Python 3.13 and newer"
            )
        else:
            assert sys.version_info >= (3, 13)
            if (
                Py_GIL_DISABLED := sysconfig.get_config_var("Py_GIL_DISABLED")
            ) is None:  # pragma: no cover
                free_threading = Unknown(
                    reason="failed to introspect build configuration"
                )
            elif Py_GIL_DISABLED == 1:
                if sys._is_gil_enabled():
                    if PYTHON_GIL == "1":
                        free_threading = Disabled(
                            reason="global locking is forced by envvar PYTHON_GIL=1"
                        )
                    else:  # pragma: no cover
                        free_threading = Disabled(
                            reason=(
                                "most likely, one or more extension(s)"
                                "already loaded did not declare compatibility"
                            )
                        )
                else:
                    if PYTHON_GIL == "0":
                        free_threading = Enabled(detail="forced by envvar PYTHON_GIL=0")
                    else:
                        free_threading = Enabled(detail="no forcing detected")
            else:
                free_threading = Unavailable(
                    reason="this interpreter was built without free-threading support"
                )

        jit: Status
        if sys.version_info < (3, 13):
            jit = Unavailable(
                reason="JIT compilation only exists in Python 3.13 and newer"
            )
        elif sys.version_info[:2] == (3, 13):
            jit = Unknown(reason="no introspection API known for Python 3.13")
        else:
            assert sys.version_info >= (3, 14)
            if sys._jit.is_enabled():
                if jit_introspection == "deep":
                    jit = Active() if sys._jit.is_active() else Inactive()
                else:
                    jit = Available()
            else:
                if not sys._jit.is_available():
                    jit = Unavailable(
                        reason="this interpreter was built without JIT compilation support"
                    )
                else:
                    jit = Disabled(reason="reason is unknown")

        return frozenset(
            {
                Feature(name="free-threading", status=free_threading),
                Feature(name="JIT compilation", status=jit),
            }
        )

    def diagnostics(
        self, *, jit_introspection: Literal["stable", "deep"] = "stable"
    ) -> list[str]:
        return [
            ft.diagnostic
            for ft in sorted(
                self.snapshot(jit_introspection=jit_introspection),
                key=lambda ft: ft.name.lower(),
            )
        ]
