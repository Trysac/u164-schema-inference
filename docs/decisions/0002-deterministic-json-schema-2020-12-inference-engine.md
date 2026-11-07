# Deterministic JSON Schema 2020-12 inference engine

Status: accepted (generated, pending human review)

## Context

Teams receiving untyped JSON exports or CSV rows require robust, reproducible JSON Schema Draft 2020-12 representations without guessed statistical models or heavy external dependencies. Leading digits in identifiers such as '007' must remain strings, format detection for dates and datetimes must adhere strictly to RFC 3339, and resource limits must prevent denial-of-service through deep recursion or excessive input sizes.

## Decision

Implement schema inference purely using Python standard library components with explicit regexes for numbers, integers, and RFC 3339 timestamps. Enforce configurable depth, record, and property limits raising typed `SchemaInferenceError` instances. Sort all dictionary keys recursively to guarantee byte-stable outputs.

## Consequences

Outputs are deterministic and byte-stable across environments. Memory usage remains bounded, and CSV data preserves string semantics for leading-zero codes while correctly identifying booleans, numbers, and null tokens.
