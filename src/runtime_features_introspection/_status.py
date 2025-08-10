__all__ = [
    "Enabled", "Disabled", "Active", "Inactive", "Available", "Unavailable", "Unknown", "Status",
]

from typing import TypeAlias, Literal
from dataclasses import dataclass


# emulating a rust-style enum, where members can have different structures
@dataclass(frozen=True, slots=True, kw_only=True)
class Enabled:
    detail: str


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
Status: TypeAlias = Literal[
    Active, Inactive, Enabled, Disabled, Available, Unavailable, Unknown
]
