# Architecture

`trysac-schema-inference` is a zero-dependency Python library designed to infer deterministic JSON Schema Draft 2020-12 from JSON collections or CSV rows.

## Core Components

- **`schema_inference.infer`**: Core inference engine providing `infer_json`, `infer_csv`, `infer_value`, and `merge_schemas`.
- **`schema_inference.formats`**: Strict regular expression and calendar date validation for `date` (ISO-8601 YYYY-MM-DD) and `date-time` (RFC 3339 section 5.6).
- **`schema_inference.errors`**: Exception hierarchy centered on `SchemaInferenceError` with typed machine-readable `ErrorCode` values.
- **`schema_inference.__main__`**: CLI driver supporting CSV (with UTF-8-BOM handling), JSONL, and JSON array inputs.

## Type Merging Rules

- Types are merged as a mathematical union.
- When both `integer` and `number` are present, `integer` is dropped in favor of `number`.
- A single type is emitted as a string (e.g. `"type": "string"`), while multiple types are emitted as a lexicographically sorted list (e.g. `"type": ["integer", "null"]`).
- Required fields are computed as the intersection of present keys across records.
- Object properties are recursively merged.
- String format is preserved if and only if all observed string values match that format.
