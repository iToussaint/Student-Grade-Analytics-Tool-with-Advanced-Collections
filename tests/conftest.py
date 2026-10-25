"""Shared fixtures: a tiny dataset whose statistics are easy to verify by hand.

Student averages: Alice 95, Cara 80, Bob 65.
All scores: 90, 100, 70, 60, 80, 80 -> mean 80, median 80, mode 80.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from grade_analytics.analysis.aggregators import Dataset, build_dataset
from grade_analytics.models.entities import GradeRecord

HEADER = (
    "student_id,name,major,year,course_code,course_name,credits,"
    "semester,score\n"
)
CSV_TEXT = HEADER + """\
S1,Alice,Computer Science,2,C1,Course One,3,2024-S1,90
S1,Alice,Computer Science,2,C2,Course Two,4,2024-S2,100
S2,Bob,Mathematics,1,C1,Course One,3,2024-S1,70
S2,Bob,Mathematics,1,C2,Course Two,4,2024-S2,60
S3,Cara,Computer Science,1,C1,Course One,3,2024-S1,80
S3,Cara,Computer Science,1,C2,Course Two,4,2024-S2,80
"""

SAMPLE_DATA = (
    Path(__file__).resolve().parent.parent / "data" / "sample_grades.csv"
)


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
