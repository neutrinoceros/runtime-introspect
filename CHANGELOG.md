# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

- DOC: fix unused variable in pytest header example application
- DOC: complete usage examples
- TYP: add autocompletion support for the `FeatureSet.supports` method

## [0.2.0] - 2025-11-01

- TST: add support for Python 3.15 (alpha)
- FEAT: add a high level APIs, including:
  - a portable `runtime_feature_set` constructor function
  - a `supports` method on feature set instances, to easily query whether a
    specific feature is available
- FEAT: `CPythonFeatureSet` now includes diagnostics for `py-limited-api`

## [0.1.0] - 2025-08-17

First public, alpha version.
