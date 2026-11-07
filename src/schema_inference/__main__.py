"""CLI interface for schema-inference."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from schema_inference.errors import SchemaInferenceError
from schema_inference.infer import infer_csv, infer_json


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: read file and print inferred JSON Schema."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        sys.stderr.write("Usage: schema-inference <file.(csv|json|jsonl)>\n")
        return 2

    target_path = Path(args[0])
    if not target_path.exists():
        sys.stderr.write(f"File not found: {target_path}\n")
        return 2

    suffix = target_path.suffix.lower()
    try:
        if suffix == ".csv":
            with target_path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                schema = infer_csv([]) if reader.fieldnames is None else infer_csv(reader)
        elif suffix == ".jsonl":
            records: list[object] = []
            with target_path.open("r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, start=1):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        records.append(json.loads(line_str))
                    except json.JSONDecodeError:
                        sys.stderr.write(f"line {line_idx}: invalid JSON\n")
                        return 2
            schema = infer_json(records)
        elif suffix == ".json":
            with target_path.open("r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    sys.stderr.write("invalid JSON\n")
                    return 2
            if not isinstance(data, list):
                sys.stderr.write("JSON root must be an array of records\n")
                return 2
            schema = infer_json(data)
        else:
            sys.stderr.write(f"Unsupported file extension: {suffix}\n")
            return 2

        output = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        sys.stdout.write(output)
        return 0
    except SchemaInferenceError as err:
        sys.stderr.write(f"{err.code}: {err}\n")
        return 2
    except Exception as err:
        sys.stderr.write(f"Error: {err}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
