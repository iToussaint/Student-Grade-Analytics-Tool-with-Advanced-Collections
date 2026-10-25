"""Collection-based aggregators.

Each helper relies on a specific type from :mod:`collections`:

* ``Counter``      - grade distribution counting
* ``defaultdict``  - grouping students / scores without key checks
* ``OrderedDict``  - distributions in a fixed, meaningful order (A to F)
* ``deque``        - fixed-size window for rolling averages
"""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, DefaultDict, Dict, Iterable, List, Optional

from grade_analytics.models import (
    LETTER_GRADES,
    Course,
    Grade,
    GradeRecord,
    Student,
)


@dataclass
class Dataset:
    """Students and courses aggregated from grade records."""

    students: Dict[str, Student] = field(default_factory=dict)
    courses: Dict[str, Course] = field(default_factory=dict)
    record_count: int = 0

    def add(self, record: GradeRecord) -> None:
        """Register one record, creating its student and course on first sight.

        The first record seen for a student defines their name, major and
        year; the first record seen for a course defines its name and credits.
        """
        student = self.students.get(record.student_id)
        if student is None:
            student = Student(
                student_id=record.student_id,
                name=record.name,
                major=record.major,
                year=record.year,
            )
            self.students[record.student_id] = student
        if record.course_code not in self.courses:
            self.courses[record.course_code] = Course(
                code=record.course_code,
                name=record.course_name,
                credits=record.credits,
            )
        student.add_grade(
            Grade(
                student_id=record.student_id,
                course_code=record.course_code,
                semester=record.semester,
                score=record.score,
            )
        )
        self.record_count += 1


def build_dataset(records: Iterable[GradeRecord]) -> Dataset:
    """Aggregate records into a ``Dataset`` in a single pass.

    Accepts any iterable, so records can be streamed from a generator
    without first being stored in a list.
    """
    dataset = Dataset()
    for record in records:
        dataset.add(record)
    return dataset


def all_grades(students: Iterable[Student]) -> List[Grade]:
    """Flatten the grades of every student into a single list."""
    return [grade for student in students for grade in student.grades]


def grade_distribution(grades: Iterable[Grade]) -> Counter[str]:
    """Count how many grades fall into each letter (A-F)."""
    return Counter(grade.letter for grade in grades)


def ordered_distribution(counts: Counter[str]) -> OrderedDict[str, int]:
    """Return a distribution ordered A to F, including empty letters.

    ``Counter`` only stores letters that occurred and keeps them in
    insertion order, so reports use an ``OrderedDict`` to guarantee a
    stable, complete A-F layout.
    """
    return OrderedDict(
        (letter, counts.get(letter, 0)) for letter in LETTER_GRADES
    )


def group_by_major(
    students: Iterable[Student],
) -> DefaultDict[str, List[Student]]:
    """Group students by their major."""
    groups: DefaultDict[str, List[Student]] = defaultdict(list)
    for student in students:
        groups[student.major].append(student)
    return groups


def group_by_year(
    students: Iterable[Student],
) -> DefaultDict[int, List[Student]]:
    """Group students by their academic year."""
    groups: DefaultDict[int, List[Student]] = defaultdict(list)
    for student in students:
        groups[student.year].append(student)
    return groups


def scores_by_course(grades: Iterable[Grade]) -> DefaultDict[str, List[float]]:
    """Map each course code to the list of scores obtained in it."""
    scores: DefaultDict[str, List[float]] = defaultdict(list)
    for grade in grades:
        scores[grade.course_code].append(grade.score)
    return scores


def scores_by_semester(
    grades: Iterable[Grade],
) -> DefaultDict[str, List[float]]:
    """Map each semester to the list of scores obtained in it."""
    scores: DefaultDict[str, List[float]] = defaultdict(list)
    for grade in grades:
        scores[grade.semester].append(grade.score)
    return scores


class RollingAverage:
    """Average of the last ``window`` values added.

    Backed by a ``deque`` with ``maxlen``: appending is O(1) and the oldest
    value is discarded automatically once the window is full. A running
    total avoids re-summing the window on every update.
    """

    def __init__(self, window: int) -> None:
        if window < 1:
            raise ValueError("window must be at least 1")
        self.window = window
        self._values: Deque[float] = deque(maxlen=window)
        self._total = 0.0

    def add(self, value: float) -> float:
        """Add a value and return the updated rolling average."""
        if len(self._values) == self.window:
            self._total -= self._values[0]
        self._values.append(value)
        self._total += value
        return self._total / len(self._values)

    @property
    def average(self) -> Optional[float]:
        """Current rolling average, or ``None`` if no value was added."""
        if not self._values:
            return None
        return self._total / len(self._values)

    @property
    def values(self) -> List[float]:
        """Values currently inside the window, oldest first."""
        return list(self._values)

    def __len__(self) -> int:
        return len(self._values)
