__all__ = ["CPythonFeatureSet", "Feature", "runtime_feature_set"]
import sys

from ._features import CPythonFeatureSet, DummyFeatureSet, Feature, FeatureSet


def runtime_feature_set() -> FeatureSet:
    """Create the feature set instance most appropriate to the runtime interpreter"""
    match sys.implementation.name:
        case "cpython":
            return CPythonFeatureSet()
        case _:
            return DummyFeatureSet()
