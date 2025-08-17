# `runtime_introspect`

[![PyPI](https://img.shields.io/pypi/v/runtime-introspect.svg?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/runtime-introspect/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/runtime-introspect)](https://pypi.org/project/runtime-introspect/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A small Python library to introspect interpreter features in a couple of
portable lines of code. The core functionality is to produce diagnostics for
which optional features are (un)available, the **state** they are in (_enabled_,
_disabled_, _active_, or _inactive_), and **why**. It utilizes implementation specific
APIs to abstract away the pain of writing portable code that runs on any
configuration.


## Scope and development status

This project is currently in alpha, with a flexible scope; Only CPython
interpreter features (Free-threading and JIT) are supported at the moment.
However, the library design leaves open the possibility to add support for other
Python implementations. If you spot something missing please open a feature
request or a pull request, contributions are always welcome !


## Installation

```shell
python -m pip install runtime-introspect
```

## Usage

Here's how to produce a
```py
>>> from runtime_introspect import CPythonFeatureSet
>>> fs = CPythonFeatureSet()
>>> print("\n".join(fs.diagnostics()))
free-threading: unavailable (this interpreter was built without free-threading support)
JIT: disabled (envvar PYTHON_JIT is unset)
```


### As a `pytest` helper

You can use this library to customize `pytest` so that test session headers
showcase the runtime feature set at startup. For instance

```py
# conftest.py
import sys
import textwrap
from runtime_introspect import CPythonFeatureSet

# ...

def pytest_report_header(config, start_path) -> list[str]:
    if sys.implementation.name == "cpython":
        fs = CPythonFeatureSet()
        return [
            "CPython optional features state (snapshot):",
            textwrap.indent("\n".join(fs.diagnostics()), "  "),
        ]
    else:
        return []
```

example output (truncated)
```
===================================== test session starts ======================================
platform darwin -- Python 3.13.6, pytest-8.4.1, pluggy-1.6.0
CPython optional features state (snapshot):
  free-threading: unavailable (this interpreter was built without free-threading support)
  JIT: undetermined (no introspection API known for Python 3.13)
...
```


### Command Line Interface (CLI) examples

Outputs may (really, should) vary depending on which python interpreter is
active and how it was invoked

```
❯ python3.13 -m runtime_introspect
free-threading: unavailable (this interpreter was built without free-threading support)
JIT: disabled (envvar PYTHON_JIT is unset)
```
```
❯ PYTHON_JIT=1 python3.13 -m runtime_introspect
free-threading: unavailable (this interpreter was built without free-threading support)
JIT: enabled (by envvar PYTHON_JIT=1)
```
```
❯ python3.14t -X gil=0 -m runtime_introspect
free-threading: enabled (forced by command line option -Xgil=0)
JIT: unavailable (this interpreter was built without JIT compilation support)
```

Run `python -m runtime_introspect --help` to browse additional options.


## Additional resources

Many more details can be inspected with the standard library `sysconfig` CLI
(`python -m sysconfig`).

Also refer to
[`python-introspection`](https://pypi.org/project/python-introspection/) for a
similar tool with a different approach and focus.
