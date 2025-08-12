import re
from itertools import chain, permutations

import pytest

from runtime_introspect._status import Status


@pytest.fixture(
    params=[
        (None, None, None, "undetermined"),
        (False, None, None, "unavailable"),
        (True, None, None, "available"),
        (True, False, None, "disabled"),
        (True, True, None, "enabled"),
        (True, True, False, "inactive"),
        (True, True, True, "active"),
    ],
    ids=lambda quadruple: quadruple[3],
)
def status_quadruple(request):
    return request.param


def test_label(status_quadruple):
    available, enabled, active, expected_label = status_quadruple
    st = Status(available=available, enabled=enabled, active=active)
    assert st.label == expected_label
    assert st.details is None
    assert st.summary == expected_label


def test_logical_consistency(status_quadruple):
    available, enabled, active, _summary = status_quadruple

    # check that this combination forms a valid instance
    Status(available=available, enabled=enabled, active=active)

    # check for logical consistency
    if active is not None:
        assert enabled
    if enabled is not None:
        assert available

    if available is None:
        assert enabled is None
    if enabled is None:
        assert active is None


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
