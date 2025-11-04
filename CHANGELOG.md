# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-11-04

- FEAT: allow user-defined list of features in
  `FeatureSet.snapshot` and `FeatureSet.diagnostics`, through a new `features`
  keyword argument
- FEAT: `FeatureSet.supports` now accepts an `introspection` keyword argument
- FEAT: add a `--features` option to the CLI
- PERF: `CPythonFeatureSet.supports` now avoids unnecessary doing work (it would
  previously inspect all features)
- API: `FeatureSet.supports` now returns `None` instead of `False` when passed
  unknown feature names

## [0.2.1] - 2025-11-03

- DOC: fix unused variable in pytest header example application
- DOC: complete usage examples
- TYP: add autocompletion support for the `FeatureSet.supports` method

## [0.2.0] - 2025-11-01

- TST: add support for Python 3.15 (alpha)
- FEAT: add high level APIs, including:
  - a portable `runtime_feature_set` constructor function
  - a `supports` method on feature set instances, to easily query whether a
    specific feature is available
- FEAT: `CPythonFeatureSet` now includes diagnostics for `py-limited-api`

## [0.1.0] - 2025-08-17

First public, alpha version.
