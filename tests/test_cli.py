import sys
from itertools import chain, combinations, product

import pytest

from runtime_introspect._cli import main
from runtime_introspect._features import VALID_FEATURE_NAMES, VALID_INTROSPECTIONS

from .helpers import cpython_only, not_cpython


@cpython_only
@pytest.mark.parametrize(
    "features",
    chain(
        chain.from_iterable(
            combinations(VALID_FEATURE_NAMES, n)
            for n in range(0, len(VALID_FEATURE_NAMES) + 1)
        ),
        [("all",)],
    ),
)
@pytest.mark.parametrize(
    "introspection, debug_flag", product([None, *VALID_INTROSPECTIONS], [True, False])
)
def test_params(features, introspection, debug_flag, capsys):
    args: list[str] = []
    if features:
        args.extend(["--features", *features])
    if introspection is not None:
        args.extend(["--introspection", introspection])
    if debug_flag:
        args.append("--debug")
    ret = main(args)
    assert ret == 0

    out, err = capsys.readouterr()
    assert not err
    assert out

    match features:
        case () | ["all"]:
            expected_line_count = 3
        case _:
            for ft in features:
                assert ft in out
            expected_line_count = len(features)

    if not debug_flag:
        assert len(out.splitlines()) == expected_line_count


@not_cpython
@pytest.mark.parametrize(
    "introspection, debug_flag", product([None, *VALID_INTROSPECTIONS], [True, False])
)
def test_unsupported_impl(introspection, debug_flag, capsys):
    args: list[str] = []
    if introspection is not None:
        args.extend(["--introspection", introspection])
    if debug_flag:
        args.append("--debug")
    ret = main(args)
    assert ret == 1

    out, err = capsys.readouterr()
    assert not out
    assert err == f"Unsupported Python implementation {sys.implementation.name!r}\n"
