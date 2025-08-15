# pyright: basic
# disabling strict mode for this file because argparse is
# impossible to combine with strict type checking
import sys
from argparse import ArgumentParser
from pprint import pprint

from runtime_introspect import CPythonFeatureSet
from runtime_introspect._features import VALID_INTROSPECTIONS


def main(argv: list[str] | None = None) -> int:
    match sys.implementation.name:
        case "cpython":
            cls = CPythonFeatureSet
        case _ as unsupported:
            print(f"Unsupported Python implementation {unsupported!r}", file=sys.stderr)
            return 1
    fs = cls()

    parser = ArgumentParser(allow_abbrev=False)
    # TODO: pass this as kwarg when support for Python 3.13 is dropped
    # https://docs.python.org/3.14/library/argparse.html#suggest-on-error
    parser.suggest_on_error = True  # type: ignore

    parser.add_argument(
        "--introspection",
        required=False,
        default="stable",
        choices=VALID_INTROSPECTIONS,
        help="select introspection strategy",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print feature states using internal representations",
    )

    args = parser.parse_args(argv)

    if args.debug:
        for ft in fs.snapshot(introspection=args.introspection):
            pprint(ft)
    else:
        for diagnostic in fs.diagnostics(introspection=args.introspection):
            print(diagnostic)

    return 0
