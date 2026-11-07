"""Comprehensive tests for schema-inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from schema_inference import (
    SchemaInferenceError,
    infer_csv,
    infer_json,
    infer_value,
    merge_schemas,
)
from schema_inference.__main__ import main
from schema_inference.formats import detect_format


def test_acceptance_item_1_infer_json() -> None:
    res = infer_json([{"a": 1, "b": "x"}, {"a": 2.5}])
    assert res == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"a": {"type": "number"}, "b": {"type": "string"}},
        "required": ["a"],
    }


def test_acceptance_item_2_merging_types() -> None:
    m1 = merge_schemas(infer_value(None), infer_value(3))
    assert m1 == {"type": ["integer", "null"]}

    m2 = merge_schemas(infer_value("x"), infer_value(1))
    assert m2 == {"type": ["integer", "string"]}

    t_bool = infer_value(True)
    assert t_bool == {"type": "boolean"}
    assert t_bool.get("type") != "integer"


def test_acceptance_item_3_arrays_and_objects() -> None:
    s1 = infer_json([{"t": [1, 2]}, {"t": []}])
    assert s1["properties"]["t"] == {"type": "array", "items": {"type": "integer"}}

    s2 = infer_json([{"t": []}])
    assert s2["properties"]["t"] == {"type": "array"}
    assert "items" not in s2["properties"]["t"]

    nested = infer_json([{"nested": {"x": 1, "y": 2}}, {"nested": {"x": 3}}])
    assert nested["properties"]["nested"] == {
        "type": "object",
        "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
        "required": ["x"],
    }


def test_acceptance_item_4_dates_and_datetimes() -> None:
    s_date = infer_json(["2026-11-06", "2026-01-31"])
    assert s_date == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "string",
        "format": "date",
    }

    s_date_invalid_leap = infer_json(["2026-11-06", "2026-01-31", "2026-02-29"])
    assert s_date_invalid_leap == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "string",
    }

    s_dt = infer_json(["2026-11-06T10:00:00Z", "2026-11-06T10:00:00+02:00"])
    assert s_dt == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "string",
        "format": "date-time",
    }

    s_mix = infer_json(["2026-11-06", "2026-11-06T10:00:00Z"])
    assert s_mix == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "string",
    }


def test_acceptance_item_5_infer_csv() -> None:
    rows = [
        {"id": "007", "n": "1", "ok": "TRUE", "p": "1.5"},
        {"id": "010", "n": "", "ok": "false", "p": "2"},
    ]
    schema = infer_csv(rows)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "n": {"type": ["integer", "null"]},
            "ok": {"type": "boolean"},
            "p": {"type": "number"},
        },
        "required": ["id", "n", "ok", "p"],
    }


def test_acceptance_item_6_csv_adversarial_numbers_and_nan() -> None:
    csv_res = infer_csv([{"a": "NaN", "b": "inf", "c": "1e400"}])
    assert csv_res["properties"]["a"] == {"type": "string"}
    assert csv_res["properties"]["b"] == {"type": "string"}
    assert csv_res["properties"]["c"] == {"type": "string"}

    with pytest.raises(SchemaInferenceError) as exc_info:
        infer_json([float("nan")])
    assert exc_info.value.code == "invalid_value"

    with pytest.raises(SchemaInferenceError) as exc_info_inf:
        infer_json([float("inf")])
    assert exc_info_inf.value.code == "invalid_value"


def test_acceptance_item_7_limits() -> None:
    # Depth 33 raises 'too_deep'
    nested: Any = "val"
    for _ in range(33):
        nested = [nested]
    with pytest.raises(SchemaInferenceError) as exc_depth:
        infer_json([nested], max_depth=32)
    assert exc_depth.value.code == "too_deep"

    # 100_001 records raises 'too_many_records'
    with pytest.raises(SchemaInferenceError) as exc_rec:
        infer_json((i for i in range(100_001)), max_records=100_000)
    assert exc_rec.value.code == "too_many_records"

    with pytest.raises(SchemaInferenceError) as exc_csv_rec:
        infer_csv(({"x": "1"} for _ in range(5)), max_records=4)
    assert exc_csv_rec.value.code == "too_many_records"

    # 1_001 keys raises 'too_many_properties'
    big_dict = {f"key_{i}": i for i in range(1_001)}
    with pytest.raises(SchemaInferenceError) as exc_prop:
        infer_json([big_dict], max_properties=1_000)
    assert exc_prop.value.code == "too_many_properties"


def test_acceptance_item_8_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data_csv = tmp_path / "data.csv"
    data_csv.write_text("id,name\n007,Bond\n", encoding="utf-8")

    # First run
    rc1 = main([str(data_csv)])
    captured1 = capsys.readouterr()
    assert rc1 == 0
    assert captured1.out.endswith("\n")
    assert json.loads(captured1.out) == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
        "required": ["id", "name"],
    }

    # Second run for byte-identical output
    rc2 = main([str(data_csv)])
    captured2 = capsys.readouterr()
    assert rc2 == 0
    assert captured1.out == captured2.out

    # Missing file
    rc_missing = main([str(tmp_path / "non_existent.csv")])
    assert rc_missing == 2
    capsys.readouterr()

    # Bad jsonl line 3
    bad_jsonl = tmp_path / "bad.jsonl"
    bad_jsonl.write_text('{"a": 1}\n{"a": 2}\nNOT_JSON\n', encoding="utf-8")
    rc_bad_jsonl = main([str(bad_jsonl)])
    captured_jsonl = capsys.readouterr()
    assert rc_bad_jsonl == 2
    assert captured_jsonl.err == "line 3: invalid JSON\n"


def test_cli_json_and_edge_cases(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # CLI without args
    assert main([]) == 2
    # CLI with too many args
    assert main(["a", "b"]) == 2
    # Unsupported extension
    unsupported = tmp_path / "data.xml"
    unsupported.write_text("<test/>", encoding="utf-8")
    assert main([str(unsupported)]) == 2

    # Valid .json
    valid_json = tmp_path / "data.json"
    valid_json.write_text('[{"x": 10}]', encoding="utf-8")
    assert main([str(valid_json)]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["properties"]["x"] == {"type": "integer"}

    # Invalid JSON in .json file
    invalid_json = tmp_path / "bad.json"
    invalid_json.write_text("{broken", encoding="utf-8")
    assert main([str(invalid_json)]) == 2
    err = capsys.readouterr().err
    assert "invalid JSON" in err

    # Non-list root in .json
    dict_json = tmp_path / "dict.json"
    dict_json.write_text('{"x": 10}', encoding="utf-8")
    assert main([str(dict_json)]) == 2
    assert "array of records" in capsys.readouterr().err

    # Empty csv
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")
    assert main([str(empty_csv)]) == 0
    capsys.readouterr()

    # jsonl valid file
    valid_jsonl = tmp_path / "data.jsonl"
    valid_jsonl.write_text('{"a": 1}\n\n{"a": 2}\n', encoding="utf-8")
    assert main([str(valid_jsonl)]) == 0
    capsys.readouterr()

    # CLI with SchemaInferenceError
    deep_json = tmp_path / "deep.json"
    deep_data: Any = 1
    for _ in range(35):
        deep_data = [deep_data]
    deep_json.write_text(json.dumps([deep_data]), encoding="utf-8")
    assert main([str(deep_json)]) == 2
    err_deep = capsys.readouterr().err
    assert "too_deep" in err_deep


def test_format_detector_details() -> None:
    assert detect_format("2023-02-28") == "date"
    assert detect_format("2023-02-29") is None  # Not leap year
    assert detect_format("2024-02-29") == "date"  # Leap year
    assert detect_format("invalid-date") is None
    assert detect_format("2023-13-01") is None

    # Datetime tests
    assert detect_format("2023-05-12T14:30:00Z") == "date-time"
    assert detect_format("2023-05-12T14:30:00.123456Z") == "date-time"
    assert detect_format("2023-05-12T14:30:00+05:30") == "date-time"
    assert detect_format("2023-05-12t14:30:00-08:00") == "date-time"
    assert detect_format("2023-05-12T25:00:00Z") is None  # Hour > 23
    assert detect_format("2023-05-12T14:65:00Z") is None  # Minute > 59
    assert detect_format("2023-05-12T14:30:00+25:00") is None  # TZ hour > 23
    assert detect_format("not a date") is None


def test_empty_iterable() -> None:
    res = infer_json([])
    assert res == {"$schema": "https://json-schema.org/draft/2020-12/schema"}

    csv_res = infer_csv([])
    assert csv_res == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {},
        "required": [],
    }


def test_invalid_value_type() -> None:
    with pytest.raises(SchemaInferenceError) as exc_info:
        infer_value(object())
    assert exc_info.value.code == "invalid_value"

    with pytest.raises(SchemaInferenceError) as exc_key:
        infer_value({123: "val"})  # Non-string key
    assert exc_key.value.code == "invalid_value"


def test_merging_edge_cases() -> None:
    # Merging schemas with array items
    a1 = {"type": "array", "items": {"type": "integer"}}
    a2 = {"type": "array", "items": {"type": "string"}}
    merged = merge_schemas(a1, a2)
    assert merged == {"type": "array", "items": {"type": ["integer", "string"]}}

    # Merging array with one having items and the other not
    a3 = {"type": "array"}
    m3 = merge_schemas(a1, a3)
    assert m3 == {"type": "array", "items": {"type": "integer"}}
    m4 = merge_schemas(a3, a1)
    assert m4 == {"type": "array", "items": {"type": "integer"}}

    # Merging schemas with formats
    s_date = {"type": "string", "format": "date"}
    s_str = {"type": "string"}
    assert merge_schemas(s_date, s_str) == {"type": "string"}
    assert merge_schemas(s_str, s_date) == {"type": "string"}
    s_dt = {"type": "string", "format": "date-time"}
    assert merge_schemas(s_date, s_dt) == {"type": "string"}

    # Single type merge
    assert merge_schemas({"type": "integer"}, {"type": "integer"}) == {"type": "integer"}

    # Object merging with disjoint keys
    o1 = {"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"]}
    o2 = {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]}
    mo = merge_schemas(o1, o2)
    assert mo["properties"] == {"a": {"type": "integer"}, "b": {"type": "string"}}
    assert mo["required"] == []

    # Merge schema with no type
    assert merge_schemas({}, {"type": "integer"}) == {"type": "integer"}

    # Merge string with non-string when string has format
    s_int = {"type": "integer"}
    assert merge_schemas(s_date, s_int) == {"type": ["integer", "string"], "format": "date"}
    assert merge_schemas(s_int, s_date) == {"type": ["integer", "string"], "format": "date"}

    # infer_json with mixed types (not all objects)
    mixed_recs = infer_json([1, "a"])
    assert mixed_recs == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": ["integer", "string"],
    }
