"""Build the JSON analytics report.

The report layout is described with ``TypedDict`` classes so that mypy can
check every section. Sections whose order matters (distributions, groups,
courses, semesters) are built as ``OrderedDict`` objects so the JSON output
is stable and easy to read.
"""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone
from typing import DefaultDict, Dict, Iterable, List, Sequence, TypedDict

from grade_analytics.aggregators import (
    Dataset,
    all_grades,
    build_dataset,
    grade_distribution,
    group_by_major,
    group_by_year,
    ordered_distribution,
    scores_by_course,
)
from grade_analytics.models import Grade, GradeRecord, Student
from grade_analytics.stats import (
    RankedStudent,
    mean,
    median,
    mode,
    rank_students,
    semester_trends,
    student_trend,
    top_performers,
)

DECIMALS = 2


class ReportMetadata(TypedDict):
    """``metadata`` section: where the data came from and its size.

    Keys:
        source_file: Name of the input CSV file.
        generated_at: UTC timestamp in ISO 8601 format.
        total_records: Number of valid grade rows processed.
        total_students: Number of distinct students.
        total_courses: Number of distinct courses.
        semesters: Semesters found, in chronological order.
    """

    source_file: str
    generated_at: str
    total_records: int
    total_students: int
    total_courses: int
    semesters: List[str]


class SummaryStatistics(TypedDict):
    """``summary`` section: descriptive statistics of all scores.

    Keys:
        count: Number of scores.
        mean: Arithmetic mean.
        median: Middle value of the sorted scores.
        mode: Every most frequent score (a list, for multimodal data).
        minimum: Lowest score.
        maximum: Highest score.
    """

    count: int
    mean: float
    median: float
    mode: List[float]
    minimum: float
    maximum: float


class RankingEntry(TypedDict):
    """One student in ``rankings`` and ``top_performers``.

    Keys:
        rank: Competition rank (ties share a rank, e.g. 1, 1, 3).
        student_id: Unique student identifier.
        name: Student name.
        major: Student major.
        year: Academic year.
        average: Mean score across all of the student's grades.
        percentile: Percentile rank of the average (0-100).
        courses_taken: Number of grades the average is based on.
    """

    rank: int
    student_id: str
    name: str
    major: str
    year: int
    average: float
    percentile: float
    courses_taken: int


class GroupSummary(TypedDict):
    """Statistics of one group in ``by_major`` or ``by_year``.

    Keys:
        student_count: Number of students in the group.
        average: Mean of every score in the group.
        median: Median of every score in the group.
        grade_distribution: Count per letter grade, A to F.
    """

    student_count: int
    average: float
    median: float
    grade_distribution: Dict[str, int]


class CourseSummary(TypedDict):
    """Statistics of one course in the ``courses`` section.

    Keys:
        name: Course name.
        credits: Credit value of the course.
        enrollments: Number of grades recorded for the course.
        mean: Mean score.
        median: Median score.
        mode: Every most frequent score.
        grade_distribution: Count per letter grade, A to F.
    """

    name: str
    credits: int
    enrollments: int
    mean: float
    median: float
    mode: List[float]
    grade_distribution: Dict[str, int]


class SemesterTrendEntry(TypedDict):
    """One semester in ``semester_trends``.

    Keys:
        semester: Semester identifier, e.g. ``2024-S1``.
        average: Mean score of the semester.
        rolling_average: Mean of the last *window* semester averages.
        grade_count: Number of grades recorded in the semester.
    """

    semester: str
    average: float
    rolling_average: float
    grade_count: int


class StudentTrendEntry(TypedDict):
    """One student in ``student_trends``.

    Keys:
        student_id: Unique student identifier.
        name: Student name.
        semester_averages: Mean score per semester, chronological.
        rolling_averages: Smoothed semester averages, same order.
        direction: ``improving``, ``declining``, ``stable`` or
            ``insufficient data``.
    """

    student_id: str
    name: str
    semester_averages: Dict[str, float]
    rolling_averages: List[float]
    direction: str


class GradeReport(TypedDict):
    """Top-level structure of the JSON report."""

    metadata: ReportMetadata
    summary: SummaryStatistics
    grade_distribution: Dict[str, int]
    top_performers: List[RankingEntry]
    rankings: List[RankingEntry]
    by_major: Dict[str, GroupSummary]
    by_year: Dict[str, GroupSummary]
    courses: Dict[str, CourseSummary]
    semester_trends: List[SemesterTrendEntry]
    student_trends: List[StudentTrendEntry]
    trend_summary: Dict[str, int]


def _round(value: float) -> float:
    """Round a value to the number of decimals used in the report."""
    return round(value, DECIMALS)


def summarize_scores(scores: Sequence[float]) -> SummaryStatistics:
    """Descriptive statistics for a non-empty list of scores."""
    return {
        "count": len(scores),
        "mean": _round(mean(scores)),
        "median": _round(median(scores)),
        "mode": [_round(value) for value in mode(scores)],
        "minimum": _round(min(scores)),
        "maximum": _round(max(scores)),
    }


def _ranking_entry(entry: RankedStudent) -> RankingEntry:
    """Convert a ``RankedStudent`` into its JSON report entry."""
    return {
        "rank": entry.rank,
        "student_id": entry.student_id,
        "name": entry.name,
        "major": entry.major,
        "year": entry.year,
        "average": _round(entry.average),
        "percentile": _round(entry.percentile),
        "courses_taken": entry.courses_taken,
    }


def _group_summary(students: Sequence[Student]) -> GroupSummary:
    """Statistics for a non-empty group of students."""
    grades = all_grades(students)
    scores = [grade.score for grade in grades]
    return {
        "student_count": len(students),
        "average": _round(mean(scores)),
        "median": _round(median(scores)),
        "grade_distribution": ordered_distribution(grade_distribution(grades)),
    }


def _course_summaries(
    dataset: Dataset, grades: Sequence[Grade]
) -> Dict[str, CourseSummary]:
    """Statistics for every course, ordered by course code."""
    scores = scores_by_course(grades)
    letters_by_course: DefaultDict[str, Counter[str]] = defaultdict(Counter)
    for grade in grades:
        letters_by_course[grade.course_code][grade.letter] += 1

    summaries: OrderedDict[str, CourseSummary] = OrderedDict()
    for code in sorted(scores):
        course = dataset.courses[code]
        course_scores = scores[code]
        summaries[code] = {
            "name": course.name,
            "credits": course.credits,
            "enrollments": len(course_scores),
            "mean": _round(mean(course_scores)),
            "median": _round(median(course_scores)),
            "mode": [_round(value) for value in mode(course_scores)],
            "grade_distribution": ordered_distribution(
                letters_by_course[code]
            ),
        }
    return summaries


def build_report_from_dataset(
    dataset: Dataset,
    source_file: str,
    top_n: int = 5,
    rolling_window: int = 3,
) -> GradeReport:
    """Assemble the full report from an aggregated dataset.

    Args:
        dataset: Students and courses built from the input records.
        source_file: Name of the input file, recorded in the metadata.
        top_n: Number of students listed under ``top_performers``.
        rolling_window: Window size (in semesters) for rolling averages.

    Raises:
        ValueError: If the dataset contains no grades.
    """
    students = list(dataset.students.values())
    grades = all_grades(students)
    if not grades:
        raise ValueError("Cannot build a report from an empty dataset")

    ranked = rank_students(students)
    trends = semester_trends(grades, window=rolling_window)
    per_student = [
        student_trend(student, window=rolling_window)
        for student in sorted(students, key=lambda s: s.student_id)
    ]

    by_major: OrderedDict[str, GroupSummary] = OrderedDict(
        (major, _group_summary(group))
        for major, group in sorted(group_by_major(students).items())
    )
    by_year: OrderedDict[str, GroupSummary] = OrderedDict(
        (str(year), _group_summary(group))
        for year, group in sorted(group_by_year(students).items())
    )
    direction_counts = Counter(trend.direction for trend in per_student)

    return {
        "metadata": {
            "source_file": source_file,
            "generated_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "total_records": dataset.record_count,
            "total_students": len(students),
            "total_courses": len(dataset.courses),
            "semesters": [trend.semester for trend in trends],
        },
        "summary": summarize_scores([grade.score for grade in grades]),
        "grade_distribution": ordered_distribution(grade_distribution(grades)),
        "top_performers": [
            _ranking_entry(e) for e in top_performers(ranked, top_n)
        ],
        "rankings": [_ranking_entry(e) for e in ranked],
        "by_major": by_major,
        "by_year": by_year,
        "courses": _course_summaries(dataset, grades),
        "semester_trends": [
            {
                "semester": trend.semester,
                "average": _round(trend.average),
                "rolling_average": _round(trend.rolling_average),
                "grade_count": trend.grade_count,
            }
            for trend in trends
        ],
        "student_trends": [
            {
                "student_id": trend.student_id,
                "name": trend.name,
                "semester_averages": OrderedDict(
                    (semester, _round(value))
                    for semester, value in trend.semester_averages.items()
                ),
                "rolling_averages": [
                    _round(v) for v in trend.rolling_averages
                ],
                "direction": trend.direction,
            }
            for trend in per_student
        ],
        "trend_summary": OrderedDict(direction_counts.most_common()),
    }


def build_report(
    records: Iterable[GradeRecord],
    source_file: str,
    top_n: int = 5,
    rolling_window: int = 3,
) -> GradeReport:
    """Aggregate records (list or generator) and build the report."""
    return build_report_from_dataset(
        build_dataset(records),
        source_file=source_file,
        top_n=top_n,
        rolling_window=rolling_window,
    )
