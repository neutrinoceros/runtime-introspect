import re
from itertools import chain, permutations

import pytest

from runtime_introspect._status import Status


@pytest.mark.parametrize(
    "available, enabled, active, expected_summary",
    [
        pytest.param(None, None, None, "undetermined", id="undetermined"),
        pytest.param(False, None, None, "unavailable", id="unavailable"),
        pytest.param(True, None, None, "available", id="available"),
        pytest.param(True, False, None, "disabled", id="disabled"),
        pytest.param(True, True, None, "enabled", id="enabled"),
        pytest.param(True, True, False, "inactive", id="inactive"),
        pytest.param(True, True, True, "active", id="active"),
    ],
)
def test_status_summary(available, enabled, active, expected_summary):
    st = Status(available=available, enabled=enabled, active=active)
    assert st.summary == expected_summary


@pytest.mark.parametrize(
    "available, enabled, active, expected_msg",
    chain(
        [
            pytest.param(
                available,
                enabled,
                active,
                (
                    "Cannot instantiate a Status with "
                    "available!=True and (enabled!=None or active!=None)"
                ),
                id=f"{available}-{enabled}-{active}",
            )
            for available in (False, None)
            for enabled, active in permutations((True, False, None), 2)
            if (enabled, active) != (None, None)
        ],
        [
            pytest.param(
                True,
                enabled,
                active,
                ("Cannot instantiate a Status with enabled!=True and active!=None"),
                id=f"True-{enabled}-{active}",
            )
            for enabled in (False, None)
            for active in (True, False)
        ],
    ),
)
def test_invalid_status(available, enabled, active, expected_msg):
    with pytest.raises(ValueError, match=f"^{re.escape(expected_msg)}$"):
        Status(available=available, enabled=enabled, active=active)
