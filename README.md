# schema-inference

[![PyPI version](https://img.shields.io/pypi/v/trysac-schema-inference)](https://pypi.org/project/trysac-schema-inference/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-schema-inference)](LICENSE)
[![CI](https://github.com/Trysac/u164-schema-inference/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u164-schema-inference/actions/workflows/ci.yml)

Infer a JSON Schema 2020-12 from JSON records or CSV rows: merged types, nullability, required keys, nested objects and arrays, date and date-time formats

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-schema-inference
# or
uv add trysac-schema-inference
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import schema_inference

# normalize() trims surrounding whitespace and lower-cases the text.
print(schema_inference.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    schema_inference.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
