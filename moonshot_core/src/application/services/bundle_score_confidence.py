"""
Per-bundle mean score and t-based confidence interval over test-level aggregates.

Each bundle contributes one score per test (mean ``evaluation_accuracy`` across prompts
for that test). The standard error and interval use that sample only — not pooled across
bundles or across individual prompts.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Iterable
from typing import Any, TypedDict

import numpy as np
from scipy.stats import t


class BundleScoreConfidenceStats(TypedDict):
    sample_size: int
    tests_in_bundle: int
    mean_score: float | None
    standard_error: float | None
    margin_of_error: float | None
    t_score: float | None
    lower_bound: float | None
    upper_bound: float | None


def per_test_mean_scores_for_bundle(
    prompts: Iterable[Any],
    bundle_test_ids: Collection[int],
) -> list[float]:
    """
    One value per test in the bundle that has at least one prompt with non-null
    ``evaluation_accuracy`` (mean accuracy across prompts for that test).
    """
    allowed = set(bundle_test_ids)
    sums: dict[int, float] = defaultdict(float)
    counts: dict[int, int] = defaultdict(int)
    for p in prompts:
        tid = getattr(p, "test_id", None)
        if tid is None or tid not in allowed:
            continue
        acc = getattr(p, "evaluation_accuracy", None)
        if acc is None:
            continue
        sums[tid] += float(acc)
        counts[tid] += 1
    return [sums[tid] / counts[tid] for tid in sorted(sums.keys()) if counts[tid] > 0]


def t_confidence_interval_stats(
    values: list[float],
    alpha: float,
    *,
    tests_in_bundle: int,
) -> BundleScoreConfidenceStats:
    """
    Mean, standard error (sample SD / sqrt(n), ddof=1), t-interval margin, and bounds.

    For n < 2 the Inspect-style standard error is treated as 0; ``t_score`` is omitted.
    """
    n = len(values)
    base: BundleScoreConfidenceStats = {
        "sample_size": n,
        "tests_in_bundle": tests_in_bundle,
        "mean_score": None,
        "standard_error": None,
        "margin_of_error": None,
        "t_score": None,
        "lower_bound": None,
        "upper_bound": None,
    }
    if n == 0:
        return base
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean())
    base["mean_score"] = mean
    if n < 2:
        base["standard_error"] = 0.0
        base["margin_of_error"] = 0.0
        base["lower_bound"] = mean
        base["upper_bound"] = mean
        return base
    sample_std = float(np.std(arr, ddof=1))
    standard_error = sample_std / float(np.sqrt(n))
    df = n - 1
    t_score = float(t.ppf(1 - alpha / 2, df))
    margin_of_error = t_score * standard_error
    base["standard_error"] = standard_error
    base["margin_of_error"] = margin_of_error
    base["t_score"] = t_score
    base["lower_bound"] = mean - margin_of_error
    base["upper_bound"] = mean + margin_of_error
    return base
