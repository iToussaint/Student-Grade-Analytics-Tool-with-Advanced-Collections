"""Tests for the text-based terminal charts."""

from __future__ import annotations

from typing import List

import pytest

from grade_analytics.reporting.charts import (
    bar_chart,
    distribution_chart,
    render_summary,
    score_baseline,
)
from grade_analytics.reporting.report import GradeReport


def test_bar_chart_scales_to_width() -> None:
    chart = bar_chart({"A": 10, "B": 5, "C": 0}, "Title", width=10)
    lines = chart.splitlines()
    assert lines[0] == "Title"
    assert lines[2] == "A | ########## 10"
    assert lines[3] == "B | ##### 5"
    assert lines[4] == "C |  0"


def test_bar_chart_with_baseline() -> None:
    chart = bar_chart({"A": 80, "B": 70}, "Scores", width=10, baseline=60)
    lines = chart.splitlines()
    assert lines[0] == "Scores (axis starts at 60)"
    assert lines[2] == "A | ########## 80"
    assert lines[3] == "B | ##### 70"


@pytest.mark.parametrize(
    ("values", "expected"),
    [([68.27, 78.06], 60.0), ([70.0, 75.0], 60.0), ([72.5], 70.0),
     ([4.0, 50.0], 0.0), ([], 0.0)],
)
def test_score_baseline(values: List[float], expected: float) -> None:
    assert score_baseline(values) == expected


def test_bar_chart_without_data() -> None:
    assert "(no data)" in bar_chart({}, "Empty")


def test_distribution_chart_shows_shares() -> None:
    assert "A: 50.0%" in distribution_chart({"A": 1, "B": 1})


def test_render_summary_contains_key_sections(report: GradeReport) -> None:
    text = render_summary(report)
    headings = (
        "Grade Distribution", "Average Score by Major", "Top Performers"
    )
    for heading in headings:
        assert heading in text
    assert "Alice" in text
