__all__ = ["Status"]

from dataclasses import dataclass
from typing import Literal, TypeAlias, final

Label: TypeAlias = Literal[
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
    """
    The status of a feature.

    A complete status is represented as an ordered triplet (available, enabled, active),
    all of which can only be either True, False, or None (representing an unknown
    or undetermined state). However, only 7 of the 27 possible combinations are
    valid status, listed here from least to most specific, with corresponding labels
      - (None, None, None) : undetermined
      - (bool, None, None) : (un)available
      - (True, bool, None) : (dis|en)abled
      - (True, True, bool) : (in)active

    They are obtained following these 2 rules:
      - the only valid value to the left of a bool is True
      - the only valid value to the right of a None is another None

    or, in logical terms:
      - (in)active => enabled
      - (dis|en)abled => available

    Any status may optionally store additional details explaining how it was
    determined.

    Instances are validated on instantiation and immutable, preventing the
    existence of an invalid status. However, `dataclasses.replace` (and `copy.replace`
    in Python 3.13+) may be used to create a modified copy of an existing status.
    """

    available: bool | None
    enabled: bool | None
    active: bool | None
    details: str | None = None

    def __post_init__(self) -> None:
        # enforce logical consistency
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
    def label(self) -> Label:
        """
        A human-readable, one-word label.
        """
        if self.active is not None:
            return "active" if self.active else "inactive"
        if self.enabled is not None:
            return "enabled" if self.enabled else "disabled"
        if self.available is not None:
            return "available" if self.available else "unavailable"

        return "undetermined"

    @property
    def summary(self) -> str:
        """
        A human-readable, one-line summary, including any detailed explanation.
        """
        details = f" ({self.details})" if self.details is not None else ""
        return self.label + details
