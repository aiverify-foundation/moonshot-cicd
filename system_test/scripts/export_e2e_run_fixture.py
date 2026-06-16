#!/usr/bin/env python3
"""
Export a benchmark run subgraph from moonshot.db into a JSON fixture for E2E seeding.

Usage:
  python system_test/scripts/export_e2e_run_fixture.py \
    --source-db moonshot_core/data/database/moonshot.db \
    --run-id 3 \
    --output system_test/fixtures/e2e_run_ac1.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "system_test" / "fixtures" / "e2e_run_ac1.json"


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _fetch_all(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def export_run_fixture(source_db: Path, run_id: int) -> dict[str, Any]:
    conn = sqlite3.connect(source_db)
    conn.row_factory = sqlite3.Row

    run = conn.execute("SELECT * FROM benchmark_run WHERE id = ?", (run_id,)).fetchone()
    if run is None:
        raise ValueError(f"benchmark_run id={run_id} not found in {source_db}")
    run_dict = {k: run[k] for k in run.keys()}

    statuses = _fetch_all(
        conn, "SELECT * FROM benchmark_run_test_status WHERE run_id = ?", (run_id,)
    )
    status_ids = [s["id"] for s in statuses]
    test_ids = list({s["test_id"] for s in statuses})

    prompts: list[dict[str, Any]] = []
    if status_ids:
        placeholders = ",".join("?" * len(status_ids))
        prompts = _fetch_all(
            conn,
            f"SELECT * FROM benchmark_run_test_prompt WHERE run_test_id IN ({placeholders})",
            tuple(status_ids),
        )

    bundles = _fetch_all(
        conn, "SELECT * FROM benchmark_run_test_bundle WHERE run_id = ?", (run_id,)
    )

    tests = []
    bundle_ids: set[int] = set()
    dataset_ids: set[int] = set()
    metric_ids: set[int] = set()
    for tid in test_ids:
        test_row = conn.execute("SELECT * FROM benchmark_test WHERE id = ?", (tid,)).fetchone()
        if test_row:
            t = {k: test_row[k] for k in test_row.keys()}
            tests.append(t)
            dataset_ids.add(t["dataset_id"])
            metric_ids.add(t["metric_id"])
    for b in bundles:
        bundle_ids.add(b["test_bundle_id"])

    bundle_rows = []
    groupings = []
    for bid in bundle_ids:
        brow = conn.execute(
            "SELECT * FROM benchmark_test_bundle WHERE id = ?", (bid,)
        ).fetchone()
        if brow:
            bundle_rows.append({k: brow[k] for k in brow.keys()})
        groupings.extend(
            _fetch_all(
                conn,
                "SELECT * FROM benchmark_test_bundle_grouping WHERE test_bundle_id = ?",
                (bid,),
            )
        )

    datasets = []
    dataset_prompts = []
    for did in dataset_ids:
        drow = conn.execute(
            "SELECT * FROM benchmark_test_dataset WHERE id = ?", (did,)
        ).fetchone()
        if drow:
            datasets.append({k: drow[k] for k in drow.keys()})
        dataset_prompts.extend(
            _fetch_all(
                conn,
                "SELECT * FROM benchmark_test_dataset_prompt WHERE benchmark_test_dataset_id = ?",
                (did,),
            )
        )

    metrics = []
    for mid in metric_ids:
        mrow = conn.execute(
            "SELECT * FROM benchmark_test_metric WHERE id = ?", (mid,)
        ).fetchone()
        if mrow:
            metrics.append({k: mrow[k] for k in mrow.keys()})

    provider = None
    model = None
    config = None
    config_params: list[dict[str, Any]] = []
    if run_dict.get("llm_provider_id"):
        prow = conn.execute(
            "SELECT * FROM llm_provider WHERE id = ?", (run_dict["llm_provider_id"],)
        ).fetchone()
        if prow:
            provider = {k: prow[k] for k in prow.keys()}
    if run_dict.get("llm_provider_model_id"):
        mrow = conn.execute(
            "SELECT * FROM llm_provider_model WHERE id = ?",
            (run_dict["llm_provider_model_id"],),
        ).fetchone()
        if mrow:
            model = {k: mrow[k] for k in mrow.keys()}
    if run_dict.get("llm_provider_model_config_id"):
        crow = conn.execute(
            "SELECT * FROM llm_provider_model_config WHERE id = ?",
            (run_dict["llm_provider_model_config_id"],),
        ).fetchone()
        if crow:
            config = {k: crow[k] for k in crow.keys()}
            config_params = _fetch_all(
                conn,
                "SELECT * FROM llm_provider_model_config_parameters WHERE config_id = ?",
                (config["id"],),
            )

    conn.close()

    return {
        "source_run_id": run_id,
        "run": {k: v for k, v in run_dict.items() if k != "id"},
        "llm_provider": (
            {k: v for k, v in provider.items() if k != "id"} if provider else None
        ),
        "llm_provider_model": (
            {k: v for k, v in model.items() if k not in ("id", "llm_provider_id")}
            if model
            else None
        ),
        "llm_provider_model_config": (
            {k: v for k, v in config.items() if k not in ("id", "model_id")}
            if config
            else None
        ),
        "llm_provider_model_config_parameters": [
            {k: v for k, v in p.items() if k not in ("id", "config_id")}
            for p in config_params
        ],
        "benchmark_test_metrics": [
            {k: v for k, v in m.items() if k != "id"} for m in metrics
        ],
        "benchmark_test_datasets": [
            {k: v for k, v in d.items() if k != "id"} for d in datasets
        ],
        "benchmark_test_dataset_prompts": [
            {
                "source_id": p["id"],
                "benchmark_test_dataset_system_name": next(
                    d["system_name"]
                    for d in datasets
                    if d["id"] == p["benchmark_test_dataset_id"]
                ),
                "benchmark_test_dataset_version": next(
                    d["version"]
                    for d in datasets
                    if d["id"] == p["benchmark_test_dataset_id"]
                ),
                "prompt": p["prompt"],
                "target": p["target"],
            }
            for p in dataset_prompts
        ],
        "benchmark_test_bundles": [
            {k: v for k, v in b.items() if k != "id"} for b in bundle_rows
        ],
        "benchmark_tests": [
            {
                **{k: v for k, v in t.items() if k not in ("id", "dataset_id", "metric_id")},
                "dataset_system_name": next(
                    d["system_name"] for d in datasets if d["id"] == t["dataset_id"]
                ),
                "dataset_version": next(
                    d["version"] for d in datasets if d["id"] == t["dataset_id"]
                ),
                "metric_name": next(
                    m["name"] for m in metrics if m["id"] == t["metric_id"]
                ),
            }
            for t in tests
        ],
        "benchmark_test_bundle_groupings": [
            {
                "bundle_system_name": next(
                    b["system_name"]
                    for b in bundle_rows
                    if b["id"] == g["test_bundle_id"]
                ),
                "bundle_version": next(
                    b["version"] for b in bundle_rows if b["id"] == g["test_bundle_id"]
                ),
                "test_system_name": next(
                    t["system_name"]
                    for t in tests
                    if t["id"] == g["test_id"]
                ),
                "test_version": next(
                    t["version"] for t in tests if t["id"] == g["test_id"]
                ),
            }
            for g in groupings
        ],
        "run_test_status": [
            {
                **{
                    k: v
                    for k, v in s.items()
                    if k not in ("id", "run_id", "test_id")
                },
                "test_system_name": next(
                    t["system_name"] for t in tests if t["id"] == s["test_id"]
                ),
                "test_version": next(
                    t["version"] for t in tests if t["id"] == s["test_id"]
                ),
            }
            for s in statuses
        ],
        "run_test_prompts": [
            {
                **{
                    k: v
                    for k, v in p.items()
                    if k not in ("id", "run_test_id", "prompt_id")
                },
                "test_system_name": next(
                    t["system_name"]
                    for t in tests
                    for s in statuses
                    if s["id"] == p["run_test_id"] and t["id"] == s["test_id"]
                ),
                "test_version": next(
                    t["version"]
                    for t in tests
                    for s in statuses
                    if s["id"] == p["run_test_id"] and t["id"] == s["test_id"]
                ),
                "source_dataset_prompt_id": p["prompt_id"],
            }
            for p in prompts
        ],
        "run_test_bundle": [
            {
                "bundle_system_name": next(
                    b["system_name"]
                    for b in bundle_rows
                    if b["id"] == rb["test_bundle_id"]
                ),
                "bundle_version": next(
                    b["version"] for b in bundle_rows if b["id"] == rb["test_bundle_id"]
                ),
                "test_system_name": next(
                    t["system_name"] for t in tests if t["id"] == rb["test_id"]
                ),
                "test_version": next(
                    t["version"] for t in tests if t["id"] == rb["test_id"]
                ),
            }
            for rb in bundles
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export benchmark run fixture JSON")
    parser.add_argument(
        "--source-db",
        type=Path,
        default=REPO_ROOT / "moonshot_core" / "data" / "database" / "moonshot.db",
    )
    parser.add_argument("--run-id", type=int, default=3)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.source_db.exists():
        print(f"error: source db not found: {args.source_db}")
        return 1

    payload = export_run_fixture(args.source_db, args.run_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"Wrote fixture for run {payload['run']['name']!r} "
        f"({len(payload['run_test_prompts'])} prompts) to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
