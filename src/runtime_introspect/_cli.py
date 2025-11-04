# pyright: basic
# disabling strict mode for this file because argparse is
# impossible to combine with strict type checking
import sys
from argparse import ArgumentParser
from pprint import pprint

from runtime_introspect import runtime_feature_set
from runtime_introspect._features import (
    VALID_FEATURE_NAMES,
    VALID_INTROSPECTIONS,
    DummyFeatureSet,
)


def main(argv: list[str] | None = None) -> int:
    fs = runtime_feature_set()
    if isinstance(fs, DummyFeatureSet):
        print(
            f"Unsupported Python implementation {sys.implementation.name!r}",
            file=sys.stderr,
        )
        return 1

    parser = ArgumentParser(allow_abbrev=False)
    # TODO: pass this as kwarg when support for Python 3.13 is dropped
    # https://docs.python.org/3.14/library/argparse.html#suggest-on-error
    parser.suggest_on_error = True  # type: ignore

    parser.add_argument(
        "--features",
        required=False,
        default="all",
        nargs="+",
        choices=VALID_FEATURE_NAMES + ["all"],
        help="select specific features (default: all)",
    )
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

    match args.features:
        case ["all"]:
            features = "all"
        case _:
            features = args.features

    if args.debug:
        for ft in fs.snapshot(
            features=features,  # type: ignore
            introspection=args.introspection,
        ):
            pprint(ft)
    else:
        for diagnostic in fs.diagnostics(
            features=features,  # type: ignore
            introspection=args.introspection,
        ):
            print(diagnostic)

    return 0
