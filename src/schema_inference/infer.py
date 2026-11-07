"""Inference and schema merging implementation."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

from schema_inference.errors import SchemaInferenceError
from schema_inference.formats import detect_format

SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

# CSV regexes
_CSV_INTEGER_RE = re.compile(r"^[+-]?(0|[1-9][0-9]*)$")
_CSV_NUMBER_RE = re.compile(
    r"^[+-]?([0-9]+\.[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?$|^[+-]?[0-9]+[eE][+-]?[0-9]+$"
)


def _sort_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively return dict with sorted keys."""
    res: dict[str, Any] = {}
    for k in sorted(d.keys()):
        v = d[k]
        if isinstance(v, dict):
            res[k] = _sort_dict(v)
        elif isinstance(v, list):
            res[k] = [_sort_dict(item) if isinstance(item, dict) else item for item in v]
        else:
            res[k] = v
    return res


def infer_value(value: Any, *, max_depth: int = 32) -> dict[str, Any]:
    """Infer JSON schema for a single decoded JSON value without $schema."""
    return _infer_val(value, depth=1, max_depth=max_depth, max_properties=1_000)


def _infer_val(
    value: Any,
    *,
    depth: int,
    max_depth: int,
    max_properties: int,
) -> dict[str, Any]:
    if depth > max_depth:
        raise SchemaInferenceError(
            "too_deep", f"Recursion depth {depth} exceeds max_depth {max_depth}"
        )

    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SchemaInferenceError("invalid_value", f"Non-finite float value: {value}")
        return {"type": "number"}
    if isinstance(value, str):
        fmt = detect_format(value)
        if fmt is not None:
            return {"type": "string", "format": fmt}
        return {"type": "string"}
    if isinstance(value, list):
        # Container depth check for list elements
        if not value:
            return {"type": "array"}
        items_schema: dict[str, Any] | None = None
        for elem in value:
            elem_schema = _infer_val(
                elem, depth=depth + 1, max_depth=max_depth, max_properties=max_properties
            )
            if items_schema is None:
                items_schema = elem_schema
            else:
                items_schema = merge_schemas(items_schema, elem_schema)
        res: dict[str, Any] = {"type": "array"}
        if items_schema is not None:
            res["items"] = items_schema
        return _sort_dict(res)
    if isinstance(value, dict):
        if len(value) > max_properties:
            raise SchemaInferenceError(
                "too_many_properties",
                f"Property count {len(value)} exceeds max_properties {max_properties}",
            )
        properties: dict[str, Any] = {}
        required = sorted(value.keys())
        for k in required:
            if not isinstance(k, str):
                raise SchemaInferenceError(
                    "invalid_value", f"Object key must be string, got {type(k)}"
                )
            properties[k] = _infer_val(
                value[k], depth=depth + 1, max_depth=max_depth, max_properties=max_properties
            )
        out: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }
        return _sort_dict(out)

    raise SchemaInferenceError("invalid_value", f"Unsupported type: {type(value)}")


def _types_of(s: dict[str, Any]) -> set[str]:
    t = s.get("type")
    if t is None:
        return set()
    if isinstance(t, str):
        return {t}
    if isinstance(t, list):
        return set(t)
    return set()


def merge_schemas(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Merge two schemas produced by this library."""
    types = _types_of(a) | _types_of(b)
    if "number" in types and "integer" in types:
        types.remove("integer")

    out: dict[str, Any] = {}
    if len(types) == 1:
        out["type"] = next(iter(types))
    elif len(types) > 1:
        out["type"] = sorted(types)

    # Object merging
    if "object" in types:
        props_a = a.get("properties", {})
        props_b = b.get("properties", {})
        all_prop_names = sorted(set(props_a.keys()) | set(props_b.keys()))
        merged_props: dict[str, Any] = {}
        for name in all_prop_names:
            if name in props_a and name in props_b:
                merged_props[name] = merge_schemas(props_a[name], props_b[name])
            elif name in props_a:
                merged_props[name] = _sort_dict(dict(props_a[name]))
            else:
                merged_props[name] = _sort_dict(dict(props_b[name]))
        out["properties"] = merged_props

        # Required keys: keys present in every object value seen
        req_a = set(a.get("required", [])) if "required" in a else set(props_a.keys())
        req_b = set(b.get("required", [])) if "required" in b else set(props_b.keys())
        merged_req = sorted(req_a & req_b)
        out["required"] = merged_req

    # Array merging
    if "array" in types:
        items_a = a.get("items")
        items_b = b.get("items")
        if items_a is not None and items_b is not None:
            out["items"] = merge_schemas(items_a, items_b)
        elif items_a is not None:
            out["items"] = _sort_dict(dict(items_a))
        elif items_b is not None:
            out["items"] = _sort_dict(dict(items_b))

    # String format merging: keep format only when every string seen has the same format
    if "string" in types:
        has_str_a = "string" in _types_of(a)
        has_str_b = "string" in _types_of(b)
        fmt_a = a.get("format") if has_str_a else None
        fmt_b = b.get("format") if has_str_b else None
        if has_str_a and has_str_b:
            if fmt_a and fmt_b and fmt_a == fmt_b:
                out["format"] = fmt_a
        elif has_str_a and fmt_a:
            out["format"] = fmt_a
        elif has_str_b and fmt_b:
            out["format"] = fmt_b

    return _sort_dict(out)


def infer_json(
    records: Iterable[Any],
    *,
    max_records: int = 100_000,
    max_depth: int = 32,
    max_properties: int = 1_000,
) -> dict[str, Any]:
    """Infer JSON Schema Draft 2020-12 from an iterable of records."""
    all_objects = True
    merged_schema: dict[str, Any] | None = None

    for record_count, rec in enumerate(records, start=1):
        if record_count > max_records:
            raise SchemaInferenceError(
                "too_many_records",
                f"Record count exceeded max_records {max_records}",
            )
        if not isinstance(rec, dict):
            all_objects = False
        rec_schema = _infer_val(rec, depth=1, max_depth=max_depth, max_properties=max_properties)
        if merged_schema is None:
            merged_schema = rec_schema
        else:
            merged_schema = merge_schemas(merged_schema, rec_schema)

    if merged_schema is None:
        # Empty iterable: produces empty schema with draft uri
        return {"$schema": SCHEMA_URI}

    out = dict(merged_schema)
    if all_objects and out.get("type") != "object":
        out["type"] = "object"
    res = {"$schema": SCHEMA_URI}
    res.update(out)
    return _sort_dict(res)


def _infer_csv_cell(val: str, null_tokens: frozenset[str]) -> dict[str, Any]:
    if val in null_tokens:
        return {"type": "null"}
    if val.lower() in ("true", "false"):
        return {"type": "boolean"}
    if _CSV_INTEGER_RE.match(val):
        return {"type": "integer"}
    if _CSV_NUMBER_RE.match(val):
        try:
            f = float(val)
            if math.isfinite(f):
                return {"type": "number"}
        except ValueError:
            pass
    fmt = detect_format(val)
    if fmt is not None:
        return {"type": "string", "format": fmt}
    return {"type": "string"}


def infer_csv(
    rows: Iterable[Mapping[str, str]],
    *,
    null_tokens: frozenset[str] = frozenset({"", "NA", "N/A", "null", "NULL"}),
    max_records: int = 100_000,
) -> dict[str, Any]:
    """Infer JSON Schema Draft 2020-12 from CSV rows."""
    properties: dict[str, dict[str, Any]] = {}
    first_row = True
    header_keys: list[str] = []

    for record_count, row in enumerate(rows, start=1):
        if record_count > max_records:
            raise SchemaInferenceError(
                "too_many_records",
                f"Record count exceeded max_records {max_records}",
            )
        if first_row:
            header_keys = list(row.keys())
            first_row = False
            for k in header_keys:
                properties[k] = _infer_csv_cell(str(row[k]), null_tokens)
        else:
            for k in header_keys:
                cell_val = str(row.get(k, ""))
                cell_schema = _infer_csv_cell(cell_val, null_tokens)
                properties[k] = merge_schemas(properties[k], cell_schema)

    if first_row:
        # No rows
        return {"$schema": SCHEMA_URI, "type": "object", "properties": {}, "required": []}

    sorted_keys = sorted(header_keys)
    out: dict[str, Any] = {
        "$schema": SCHEMA_URI,
        "type": "object",
        "properties": {k: properties[k] for k in sorted_keys},
        "required": sorted_keys,
    }
    return _sort_dict(out)
