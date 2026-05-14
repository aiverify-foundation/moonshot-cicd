"""
Prompt-level scores and t-based confidence intervals for benchmark run results.

``t_confidence_interval_stats`` operates on a list of numeric scores (typically
per-prompt ``score`` values). ``margin_of_error_by_test`` groups prompts by
``test_id`` and applies the same interval rule per test (two or fewer scored prompts
in that test → margin ``0.0``).
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
    ``score`` (mean across prompts for that test).
    """
    allowed = set(bundle_test_ids)
    sums: dict[int, float] = defaultdict(float)
    counts: dict[int, int] = defaultdict(int)
    for p in prompts:
        tid = getattr(p, "test_id", None)
        if tid is None or tid not in allowed:
            continue
        s = getattr(p, "score", None)
        if s is None:
            continue
        sums[tid] += float(s)
        counts[tid] += 1
    return [sums[tid] / counts[tid] for tid in sorted(sums.keys()) if counts[tid] > 0]


def per_prompt_scores_for_bundle(
    prompts: Iterable[Any],
    bundle_test_ids: Collection[int],
) -> list[float]:
    """
    One value per prompt row in the bundle's tests with non-null ``score``.

    Order matches ``prompts`` iteration order.
    """
    allowed = set(bundle_test_ids)
    out: list[float] = []
    for p in prompts:
        tid = getattr(p, "test_id", None)
        if tid is None or tid not in allowed:
            continue
        s = getattr(p, "score", None)
        if s is None:
            continue
        out.append(float(s))
    return out


def margin_of_error_by_test(
    prompts: Iterable[Any],
    alpha: float,
) -> list[tuple[int, float]]:
    """
    For each ``test_id`` that appears on any prompt row in the run, return the half-width
    of a 95% (when ``alpha`` is 0.05) t-interval on the mean of that test's prompt
    ``score`` values. Tests with two or fewer scored prompts get margin ``0.0``.
    """
    rows = list(prompts)
    test_ids_seen = sorted(
        {int(tid) for p in rows if (tid := getattr(p, "test_id", None)) is not None}
    )
    by_test: dict[int, list[float]] = defaultdict(list)
    for p in rows:
        tid = getattr(p, "test_id", None)
        if tid is None:
            continue
        s = getattr(p, "score", None)
        if s is None:
            continue
        by_test[int(tid)].append(float(s))
    out: list[tuple[int, float]] = []
    for tid in test_ids_seen:
        values = by_test.get(tid, [])
        stats = t_confidence_interval_stats(
            values,
            alpha,
            tests_in_bundle=1,
        )
        margin = stats["margin_of_error"]
        if len(values) <= 2:
            margin = 0.0
        elif margin is None:
            margin = 0.0
        out.append((tid, float(margin)))
    return out


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
