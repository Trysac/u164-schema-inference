"""Infer JSON Schema Draft 2020-12 from JSON records or CSV rows."""

from __future__ import annotations

import logging

from schema_inference.errors import ErrorCode, SchemaInferenceError
from schema_inference.infer import infer_csv, infer_json, infer_value, merge_schemas

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"
__all__ = [
    "ErrorCode",
    "SchemaInferenceError",
    "__version__",
    "infer_csv",
    "infer_json",
    "infer_value",
    "merge_schemas",
]
