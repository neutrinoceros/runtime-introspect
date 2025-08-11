__all__ = [
    "Active",
    "Available",
    "Disabled",
    "Enabled",
    "Inactive",
    "Status",
    "Unavailable",
    "Unknown",
]

from dataclasses import dataclass
from typing import TypeAlias


# emulating a rust-style enum, where members can have different structures
@dataclass(frozen=True, slots=True, kw_only=True)
class Enabled:
    detail: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class Disabled:
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Active: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Inactive: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Available: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Unavailable:
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Unknown:
    reason: str


# sorted from most to least accurate (privative prefixes come last in cases of equal accuracy)
Status: TypeAlias = (
    Active | Inactive | Enabled | Disabled | Available | Unavailable | Unknown
)
