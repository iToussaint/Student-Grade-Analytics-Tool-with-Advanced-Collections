"""Fixtures shared by the unit and integration test suites."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from grade_analytics.analysis.aggregators import Dataset, build_dataset
from grade_analytics.models.entities import GradeRecord
from grade_analytics.reporting.report import GradeReport, build_report

from tests.helpers import CSV_TEXT


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """The tiny dataset written to a temporary CSV file."""
    path = tmp_path / "grades.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def records() -> List[GradeRecord]:
    """The tiny dataset as ``GradeRecord`` tuples."""
    rows = [line.split(",") for line in CSV_TEXT.strip().splitlines()[1:]]
    return [
        GradeRecord(
            sid, name, major, int(year), code, cname, int(credits), sem,
            float(score),
        )
        for sid, name, major, year, code, cname, credits, sem, score in rows
    ]


@pytest.fixture
def dataset(records: List[GradeRecord]) -> Dataset:
    """The tiny dataset aggregated into students and courses."""
    return build_dataset(records)


@pytest.fixture
def report(records: List[GradeRecord]) -> GradeReport:
    """Report built from the tiny dataset (top 2, 2-semester window)."""
    return build_report(
        records, source_file="grades.csv", top_n=2, rolling_window=2
    )
