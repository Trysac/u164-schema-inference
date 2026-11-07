"""Exceptions and error codes for schema inference."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal[
    "invalid_value",
    "too_deep",
    "too_many_records",
    "too_many_properties",
    "invalid_input",
]


class SchemaInferenceError(Exception):
    """Base error raised during schema inference."""

    def __init__(self, code: ErrorCode, message: str = "") -> None:
        self.code: ErrorCode = code
        safe_msg = (message[:200] if len(message) > 200 else message) if message else str(code)
        super().__init__(safe_msg)
