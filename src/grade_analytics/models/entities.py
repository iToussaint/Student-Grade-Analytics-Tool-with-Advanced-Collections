"""Data models for the grade analytics tool.

The domain is represented with ``dataclasses`` (``Student``, ``Course``,
``Grade``) and a lightweight ``namedtuple`` (``GradeRecord``) for the raw,
immutable rows read from CSV files.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, NamedTuple, Optional, Union

# A numeric score may arrive as text (CSV) or as a number (code / JSON).
ScoreInput = Union[str, int, float]

MIN_SCORE: float = 0.0
MAX_SCORE: float = 100.0

# Lower bound (inclusive) of each letter grade, best grade first.
LETTER_THRESHOLDS: Dict[str, float] = {
    "A": 90.0,
    "B": 80.0,
    "C": 70.0,
    "D": 60.0,
    "F": 0.0,
}
LETTER_GRADES: List[str] = list(LETTER_THRESHOLDS)


def parse_score(value: ScoreInput) -> float:
    """Convert a raw score to a float and validate its range.

    Args:
        value: Score as a string, int or float.

    Returns:
        The score as a float.

    Raises:
        ValueError: If the value is not numeric or outside 0-100.
    """
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid score: {value!r}") from exc
    if not MIN_SCORE <= score <= MAX_SCORE:
        raise ValueError(
            f"Score {score} is outside the range {MIN_SCORE}-{MAX_SCORE}"
        )
    return score


def letter_for(score: float) -> str:
    """Return the letter grade (A-F) for a numeric score."""
    for letter, threshold in LETTER_THRESHOLDS.items():
        if score >= threshold:
            return letter
    return LETTER_GRADES[-1]


class GradeRecord(NamedTuple):
    """One raw, validated row of the input CSV file.

    A ``namedtuple`` is used because rows are immutable and very numerous:
    it has the memory footprint of a plain tuple while keeping named access.
    """

    student_id: str
    name: str
    major: str
    year: int
    course_code: str
    course_name: str
    credits: int
    semester: str
    score: float


@dataclass(frozen=True, slots=True)
class Course:
    """A course offered by the institution."""

    code: str
    name: str
    credits: int


@dataclass(frozen=True, slots=True)
class Grade:
    """A score obtained by a student in a course during a semester."""

    student_id: str
    course_code: str
    semester: str
    score: float

    @property
    def letter(self) -> str:
        """Letter grade (A-F) corresponding to the score."""
        return letter_for(self.score)


@dataclass(slots=True)
class Student:
    """A student together with every grade they have received."""

    student_id: str
    name: str
    major: str
    year: int
    grades: List[Grade] = field(default_factory=list)

    def add_grade(self, grade: Grade) -> None:
        """Attach a grade to this student.

        Raises:
            ValueError: If the grade belongs to another student.
        """
        if grade.student_id != self.student_id:
            raise ValueError(
                f"Grade for {grade.student_id} cannot be added to "
                f"{self.student_id}"
            )
        self.grades.append(grade)

    @property
    def average(self) -> Optional[float]:
        """Mean score across all grades, or ``None`` if there are none."""
        if not self.grades:
            return None
        return sum(g.score for g in self.grades) / len(self.grades)

    def best_grade(self) -> Optional[Grade]:
        """Highest grade received, or ``None`` if there are none."""
        if not self.grades:
            return None
        return max(self.grades, key=lambda g: g.score)

    def grade_for(self, course_code: str, semester: str) -> Optional[Grade]:
        """Find the grade for a course in a semester, if it exists."""
        for grade in self.grades:
            if grade.course_code == course_code and grade.semester == semester:
                return grade
        return None

    def semester_averages(self) -> Dict[str, float]:
        """Mean score per semester, ordered chronologically."""
        totals: Dict[str, List[float]] = defaultdict(list)
        for grade in self.grades:
            totals[grade.semester].append(grade.score)
        return {
            semester: sum(scores) / len(scores)
            for semester, scores in sorted(totals.items())
        }
