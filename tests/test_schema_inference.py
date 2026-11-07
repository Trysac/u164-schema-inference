"""Behavior tests for the public API of schema_inference."""

from __future__ import annotations

import pytest

import schema_inference


def test_normalize_trims_and_lowercases() -> None:
    assert schema_inference.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        schema_inference.normalize(value)


def test_version_is_semver() -> None:
    parts = schema_inference.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
