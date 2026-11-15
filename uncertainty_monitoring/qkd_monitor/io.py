"""Strict, auditable JSON/JSONL files; no pickle or dynamic evaluation."""
import json
from pathlib import Path


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def write_jsonl(path, rows):
    with Path(path).open("w",encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row,allow_nan=False,separators=(",",":"))+"\n")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        for number,line in enumerate(handle,1):
            if not line.strip():
                continue
            try:
                yield json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON: {value}")))
            except (ValueError,TypeError) as exc:
                raise ValueError(f"Invalid JSONL at line {number}: {exc}") from exc
