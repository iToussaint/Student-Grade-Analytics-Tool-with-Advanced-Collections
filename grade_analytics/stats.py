"""Statistics: central tendency, percentiles, rankings and trends."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, OrderedDict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from grade_analytics.aggregators import RollingAverage, scores_by_semester
from grade_analytics.models import Grade, Student

# Minimum change (in score points) for a trend to count as a real movement.
TREND_THRESHOLD: float = 1.0


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean.

    Raises:
        ValueError: If ``values`` is empty.
    """
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values) / len(values)


def median(values: Sequence[float]) -> float:
    """Middle value of the sorted data (average of the two middles if even).

    Raises:
        ValueError: If ``values`` is empty.
    """
    if not values:
        raise ValueError("median() requires at least one value")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def mode(values: Iterable[float]) -> List[float]:
    """Most frequent value(s), computed with ``Counter``.

    All values sharing the highest frequency are returned in ascending
    order, so multimodal data is reported faithfully.

    Raises:
        ValueError: If ``values`` is empty.
    """
    counts = Counter(values)
    if not counts:
        raise ValueError("mode() requires at least one value")
    highest = max(counts.values())
    return sorted(value for value, count in counts.items() if count == highest)


def percentile_rank(value: float, population: Sequence[float]) -> float:
    """Percentile rank of ``value`` within ``population`` (0-100).

    Uses the standard definition: the percentage of values below ``value``
    plus half of the values equal to it.

    Raises:
        ValueError: If ``population`` is empty.
    """
    if not population:
        raise ValueError("percentile_rank() requires a non-empty population")
    ordered = sorted(population)
    return _percentile_from_sorted(value, ordered)


def _percentile_from_sorted(value: float, ordered: Sequence[float]) -> float:
    """Percentile rank of ``value`` in an already sorted population."""
    below = bisect_left(ordered, value)
    equal = bisect_right(ordered, value) - below
    return 100.0 * (below + 0.5 * equal) / len(ordered)


def percentile_ranks(scores: Mapping[str, float]) -> Dict[str, float]:
    """Percentile rank of every entry, sorting the population only once."""
    ordered = sorted(scores.values())
    return {
        key: _percentile_from_sorted(value, ordered)
        for key, value in scores.items()
    }


@dataclass(frozen=True, slots=True)
class RankedStudent:
    """A student's position in the overall ranking."""

    rank: int
    student_id: str
    name: str
    major: str
    year: int
    average: float
    percentile: float
    courses_taken: int


def rank_students(students: Iterable[Student]) -> List[RankedStudent]:
    """Rank students by average score, best first.

    Uses standard competition ranking ("1224"): students with equal averages
    share a rank and the next rank is skipped accordingly. Ties are listed
    by student id for a deterministic order. Students without grades are
    excluded.
    """
    averages: Dict[str, float] = {}
    by_id: Dict[str, Student] = {}
    for student in students:
        average = student.average
        if average is not None:
            averages[student.student_id] = average
            by_id[student.student_id] = student

    percentiles = percentile_ranks(averages)
    ordered_ids = sorted(averages, key=lambda sid: (-averages[sid], sid))

    ranked: List[RankedStudent] = []
    previous_average: Optional[float] = None
    current_rank = 0
    for position, student_id in enumerate(ordered_ids, start=1):
        average = averages[student_id]
        if average != previous_average:
            current_rank = position
            previous_average = average
        student = by_id[student_id]
        ranked.append(
            RankedStudent(
                rank=current_rank,
                student_id=student_id,
                name=student.name,
                major=student.major,
                year=student.year,
                average=average,
                percentile=percentiles[student_id],
                courses_taken=len(student.grades),
            )
        )
    return ranked


def top_performers(
    ranked: Sequence[RankedStudent], count: int
) -> List[RankedStudent]:
    """The first ``count`` students of an existing ranking."""
    if count < 0:
        raise ValueError("count must not be negative")
    return list(ranked[:count])


@dataclass(frozen=True, slots=True)
class SemesterTrend:
    """Average score of a semester and the rolling average up to it."""

    semester: str
    average: float
    rolling_average: float
    grade_count: int


def semester_trends(
    grades: Iterable[Grade], window: int = 3
) -> List[SemesterTrend]:
    """Average per semester plus a ``deque``-backed rolling average.

    Semesters are processed chronologically (their identifiers, such as
    ``2024-S1``, sort in time order).
    """
    by_semester = scores_by_semester(grades)
    rolling = RollingAverage(window)
    trends: List[SemesterTrend] = []
    for semester in sorted(by_semester):
        scores = by_semester[semester]
        semester_average = mean(scores)
        trends.append(
            SemesterTrend(
                semester=semester,
                average=semester_average,
                rolling_average=rolling.add(semester_average),
                grade_count=len(scores),
            )
        )
    return trends


def trend_direction(
    values: Sequence[float], threshold: float = TREND_THRESHOLD
) -> str:
    """Classify a chronological series as improving, declining or stable.

    Compares the last value with the first. A series with fewer than two
    values is reported as ``"insufficient data"``.
    """
    if len(values) < 2:
        return "insufficient data"
    change = values[-1] - values[0]
    if change > threshold:
        return "improving"
    if change < -threshold:
        return "declining"
    return "stable"


@dataclass(frozen=True, slots=True)
class StudentTrend:
    """How a single student's results evolve over semesters."""

    student_id: str
    name: str
    semester_averages: OrderedDict[str, float]
    rolling_averages: List[float]
    direction: str


def student_trend(student: Student, window: int = 2) -> StudentTrend:
    """Track one student's semester averages with a rolling average.

    The direction is computed on the smoothed (rolling) series so that a
    single unusual semester does not dominate the result.
    """
    per_semester = OrderedDict(student.semester_averages())
    rolling = RollingAverage(window)
    smoothed = [rolling.add(value) for value in per_semester.values()]
    return StudentTrend(
        student_id=student.student_id,
        name=student.name,
        semester_averages=per_semester,
        rolling_averages=smoothed,
        direction=trend_direction(smoothed),
    )
