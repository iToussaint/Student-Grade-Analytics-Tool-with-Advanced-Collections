"""Tests for the JSON report builder and console rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from grade_analytics.analysis.aggregators import Dataset
from grade_analytics.io.files import iter_records, write_json
from grade_analytics.models.entities import GradeRecord
from grade_analytics.reporting.report import (
    GradeReport,
    build_report,
    build_report_from_dataset,
)
from grade_analytics.reporting.charts import (
    bar_chart,
    distribution_chart,
    render_summary,
    score_baseline,
)

from tests.conftest import SAMPLE_DATA

EXPECTED_SECTIONS = [
    "metadata",
    "summary",
    "grade_distribution",
    "top_performers",
    "rankings",
    "by_major",
    "by_year",
    "courses",
    "semester_trends",
    "student_trends",
    "trend_summary",
]


@pytest.fixture
def report(records: List[GradeRecord]) -> GradeReport:
    """Report built from the tiny dataset (top 2, 2-semester window)."""
    return build_report(
        records, source_file="grades.csv", top_n=2, rolling_window=2
    )


def test_sections_follow_typed_dict_order(report: GradeReport) -> None:
    assert list(report) == EXPECTED_SECTIONS
    assert list(GradeReport.__annotations__) == EXPECTED_SECTIONS


def test_metadata(report: GradeReport) -> None:
    meta = report["metadata"]
    assert meta["source_file"] == "grades.csv"
    assert meta["total_records"] == 6
    assert meta["total_students"] == 3
    assert meta["total_courses"] == 2
    assert meta["semesters"] == ["2024-S1", "2024-S2"]


def test_summary_statistics(report: GradeReport) -> None:
    assert report["summary"] == {
        "count": 6,
        "mean": 80.0,
        "median": 80.0,
        "mode": [80.0],
        "minimum": 60.0,
        "maximum": 100.0,
    }


def test_grade_distribution_is_complete_and_ordered(
    report: GradeReport,
) -> None:
    assert list(report["grade_distribution"].items()) == [
        ("A", 2), ("B", 2), ("C", 1), ("D", 1), ("F", 0),
    ]


def test_rankings_and_top_performers(report: GradeReport) -> None:
    assert [e["name"] for e in report["top_performers"]] == ["Alice", "Cara"]
    assert [e["rank"] for e in report["rankings"]] == [1, 2, 3]
    assert report["rankings"][0]["percentile"] == 83.33


def test_group_and_course_sections(report: GradeReport) -> None:
    assert list(report["by_major"]) == ["Computer Science", "Mathematics"]
    assert report["by_major"]["Computer Science"]["student_count"] == 2
    assert report["by_major"]["Computer Science"]["average"] == 87.5
    assert list(report["by_year"]) == ["1", "2"]
    assert report["by_year"]["1"]["average"] == 72.5
    course = report["courses"]["C2"]
    assert course["name"] == "Course Two"
    assert course["enrollments"] == 3
    assert course["mean"] == 80.0


def test_trend_sections(report: GradeReport) -> None:
    assert [t["average"] for t in report["semester_trends"]] == [80.0, 80.0]
    alice = report["student_trends"][0]
    assert alice["student_id"] == "S1"
    assert alice["rolling_averages"] == [90.0, 95.0]
    assert sum(report["trend_summary"].values()) == 3


def test_empty_dataset_raises() -> None:
    with pytest.raises(ValueError):
        build_report_from_dataset(Dataset(), source_file="empty.csv")


def test_report_is_json_serialisable(
    report: GradeReport, tmp_path: Path
) -> None:
    path = write_json(report, tmp_path / "report.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert list(loaded) == EXPECTED_SECTIONS
    assert loaded["summary"]["mean"] == 80.0


def test_sample_data_report() -> None:
    """End-to-end run on the committed sample CSV, streamed lazily."""
    report = build_report(
        iter_records(SAMPLE_DATA), source_file=SAMPLE_DATA.name
    )
    meta = report["metadata"]
    assert meta["total_students"] == 30
    assert meta["total_records"] == sum(report["grade_distribution"].values())
    assert len(report["rankings"]) == 30
    assert len(report["top_performers"]) == 5
    averages = [e["average"] for e in report["rankings"]]
    assert averages == sorted(averages, reverse=True)
    assert all(0 <= e["percentile"] <= 100 for e in report["rankings"])


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
