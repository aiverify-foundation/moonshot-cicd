#!/usr/bin/env python3
"""
Validate benchmark export JSON against GA Schema1.

Reads JSON from stdin or a file path argument. Exits 0 on success, 1 on failure.

Usage:
  python system_test/scripts/validate_schema1_json.py export.json
  echo '{"run_metadata":...}' | python system_test/scripts/validate_schema1_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from process_check_app.backend.report_validation import validate_json  # noqa: E402
from process_check_app.backend.schema.ms_ga_schema import Schema1  # noqa: E402


def validate_schema1(data: dict) -> None:
    Schema1(**data)
    if not validate_json(data):
        raise ValueError("validate_json returned False for export payload")


def main() -> int:
    try:
        if len(sys.argv) > 1:
            raw = Path(sys.argv[1]).read_text(encoding="utf-8")
        else:
            raw = sys.stdin.read()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        validate_schema1(data)
    except Exception as exc:
        print(f"Schema1 validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
