"""Unit tests for per-bundle score aggregation and t confidence intervals."""

import math

import pytest

from application.services.bundle_score_confidence import (
    margin_of_error_by_test,
    per_prompt_scores_for_bundle,
    per_test_mean_scores_for_bundle,
    t_confidence_interval_stats,
)


class _P:
    def __init__(self, test_id, score):
        self.test_id = test_id
        self.score = score


def test_per_test_mean_scores_filters_bundle_and_nulls():
    prompts = [
        _P(1, 1.0),
        _P(1, 0.0),
        _P(2, None),
        _P(99, 1.0),
    ]
    assert per_test_mean_scores_for_bundle(prompts, {1, 2}) == [0.5]


def test_per_test_mean_scores_two_tests_sorted():
    prompts = [
        _P(2, 0.4),
        _P(1, 0.2),
        _P(1, 0.8),
        _P(2, 0.6),
    ]
    assert per_test_mean_scores_for_bundle(prompts, {1, 2}) == [0.5, 0.5]


def test_per_prompt_scores_filters_bundle_and_nulls():
    prompts = [
        _P(1, 1.0),
        _P(1, 0.0),
        _P(2, None),
        _P(99, 1.0),
    ]
    assert per_prompt_scores_for_bundle(prompts, {1, 2}) == [1.0, 0.0]


def test_per_prompt_scores_order_follows_prompts():
    prompts = [_P(2, 0.4), _P(1, 0.2), _P(1, 0.8), _P(2, 0.6)]
    assert per_prompt_scores_for_bundle(prompts, {1, 2}) == [0.4, 0.2, 0.8, 0.6]


def test_margin_of_error_by_test_two_tests():
    prompts = [_P(1, 1.0), _P(1, 0.0), _P(2, 0.4), _P(2, 0.6)]
    rows = margin_of_error_by_test(prompts, 0.05)
    assert [r[0] for r in rows] == [1, 2]
    assert rows[0][1] == pytest.approx(0.0)
    assert rows[1][1] == pytest.approx(0.0)


def test_margin_of_error_by_test_three_prompts_nonzero_spread():
    prompts = [_P(10, 1.0), _P(10, 0.0), _P(10, 0.5)]
    rows = margin_of_error_by_test(prompts, 0.05)
    assert len(rows) == 1
    assert rows[0][0] == 10
    assert rows[0][1] > 0


def test_t_interval_n_zero():
    s = t_confidence_interval_stats([], 0.05, tests_in_bundle=3)
    assert s["sample_size"] == 0
    assert s["tests_in_bundle"] == 3
    assert s["mean_score"] is None


def test_t_interval_n_one_zero_width():
    s = t_confidence_interval_stats([0.7], 0.05, tests_in_bundle=1)
    assert s["sample_size"] == 1
    assert s["mean_score"] == pytest.approx(0.7)
    assert s["standard_error"] == 0.0
    assert s["margin_of_error"] == 0.0
    assert s["t_score"] is None
    assert s["lower_bound"] == pytest.approx(0.7)
    assert s["upper_bound"] == pytest.approx(0.7)


def test_t_interval_n_two_matches_scipy():
    values = [1.0, 0.0]
    s = t_confidence_interval_stats(values, 0.05, tests_in_bundle=2)
    assert s["sample_size"] == 2
    assert s["mean_score"] == pytest.approx(0.5)
    assert s["standard_error"] == pytest.approx(0.5)
    assert s["t_score"] == pytest.approx(12.706204736174697)
    assert s["margin_of_error"] == pytest.approx(s["t_score"] * s["standard_error"])
    assert s["lower_bound"] == pytest.approx(0.5 - s["margin_of_error"])
    assert s["upper_bound"] == pytest.approx(0.5 + s["margin_of_error"])
    assert math.isfinite(s["lower_bound"])
    assert math.isfinite(s["upper_bound"])
