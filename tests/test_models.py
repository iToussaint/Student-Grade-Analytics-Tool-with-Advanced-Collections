"""Tests for the dataclass / namedtuple models."""

from __future__ import annotations

import dataclasses
from typing import Union

import pytest

from grade_analytics.models import (
    Course,
    Grade,
    GradeRecord,
    Student,
    letter_for,
    parse_score,
)


@pytest.mark.parametrize(
    ("score", "letter"),
    [
        (100, "A"), (90, "A"), (89.99, "B"), (80, "B"),
        (70, "C"), (60, "D"), (59.9, "F"), (0, "F"),
    ],
)
def test_letter_for_boundaries(score: float, letter: str) -> None:
    assert letter_for(score) == letter


@pytest.mark.parametrize("raw", ["85", 85, 85.0, " 85 "])
def test_parse_score_accepts_union_inputs(raw: Union[str, int, float]) -> None:
    assert parse_score(raw) == 85.0


@pytest.mark.parametrize("raw", ["abc", "", "-1", "100.5"])
def test_parse_score_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_score(raw)


def test_grade_letter_property() -> None:
    assert Grade("S1", "C1", "2024-S1", 84.0).letter == "B"


def test_grade_and_course_are_immutable() -> None:
    grade = Grade("S1", "C1", "2024-S1", 84.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        grade.score = 99.0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        Course("C1", "Course", 3).credits = 4  # type: ignore[misc]


def test_models_use_slots() -> None:
    assert not hasattr(Grade("S1", "C1", "2024-S1", 1.0), "__dict__")
    assert not hasattr(Student("S1", "A", "CS", 1), "__dict__")


def test_grade_record_is_namedtuple() -> None:
    record = GradeRecord(
        "S1", "A", "CS", 1, "C1", "Course", 3, "2024-S1", 75.0
    )
    assert record.score == record[-1] == 75.0
    assert record._asdict()["course_code"] == "C1"


def test_student_average_and_best_grade() -> None:
    student = Student("S1", "Alice", "CS", 2)
    assert student.average is None
    assert student.best_grade() is None

    student.add_grade(Grade("S1", "C1", "2024-S1", 70.0))
    student.add_grade(Grade("S1", "C2", "2024-S1", 90.0))
    assert student.average == 80.0
    best = student.best_grade()
    assert best is not None and best.course_code == "C2"


def test_student_rejects_foreign_grade() -> None:
    with pytest.raises(ValueError):
        Student("S1", "Alice", "CS", 2).add_grade(
            Grade("S2", "C1", "2024-S1", 70.0)
        )


def test_grade_for_returns_optional() -> None:
    student = Student("S1", "Alice", "CS", 2)
    student.add_grade(Grade("S1", "C1", "2024-S1", 70.0))
    found = student.grade_for("C1", "2024-S1")
    assert found is not None and found.score == 70.0
    assert student.grade_for("C1", "2025-S1") is None


def test_semester_averages_are_chronological() -> None:
    student = Student("S1", "Alice", "CS", 2)
    student.add_grade(Grade("S1", "C3", "2024-S2", 100.0))
    student.add_grade(Grade("S1", "C1", "2024-S1", 60.0))
    student.add_grade(Grade("S1", "C2", "2024-S1", 80.0))
    assert student.semester_averages() == {"2024-S1": 70.0, "2024-S2": 100.0}
    assert list(student.semester_averages()) == ["2024-S1", "2024-S2"]
