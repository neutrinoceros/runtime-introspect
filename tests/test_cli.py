import sys
from itertools import product

import pytest

from runtime_introspect._cli import main
from runtime_introspect._features import VALID_INTROSPECTIONS

from .helpers import cpython_only, not_cpython


@cpython_only
@pytest.mark.parametrize(
    "introspection, debug_flag", product([None, *VALID_INTROSPECTIONS], [True, False])
)
def test_params(introspection, debug_flag, capsys):
    args: list[str] = []
    if introspection is not None:
        args.extend(["--introspection", introspection])
    if debug_flag:
        args.append("--debug")
    ret = main(args)
    assert ret == 0

    out, err = capsys.readouterr()
    assert not err
    assert out


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
