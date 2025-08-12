__all__ = ["Status"]

import sys
from dataclasses import dataclass
from typing import Literal, TypeAlias, final

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

Summary: TypeAlias = Literal[
    "active",
    "inactive",
    "enabled",
    "disabled",
    "available",
    "unavailable",
    "undetermined",
]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Status:
    available: bool | None
    enabled: bool | None
    active: bool | None
    details: str | None = None

    def __post_init__(self) -> None:
        if not self.available and (self.enabled is not None or self.active is not None):
            raise ValueError(
                "Cannot instantiate a Status with "
                "available!=True and (enabled!=None or active!=None)"
            )

        if not self.enabled and self.active is not None:
            raise ValueError(
                "Cannot instantiate a Status with enabled!=True and active!=None"
            )

    @property
    def summary(self) -> Summary:
        if self.active is not None:
            return "active" if self.active else "inactive"
        if self.enabled is not None:
            return "enabled" if self.enabled else "disabled"
        if self.available is not None:
            return "available" if self.available else "unavailable"

        return "undetermined"

    @override
    def __str__(self) -> str:
        details = f" ({self.details})" if self.details is not None else ""
        return self.summary + details
