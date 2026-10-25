"""Tests for the JSON report builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grade_analytics.analysis.aggregators import Dataset
from grade_analytics.io.files import write_json
from grade_analytics.reporting.report import (
    GradeReport,
    build_report_from_dataset,
)

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
