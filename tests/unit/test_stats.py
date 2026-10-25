"""Tests for statistical calculations, ranking and trend analysis."""

from __future__ import annotations

import pytest

from grade_analytics.analysis.aggregators import Dataset, all_grades
from grade_analytics.models.entities import Grade, Student
from grade_analytics.analysis.stats import (
    mean,
    median,
    mode,
    percentile_rank,
    percentile_ranks,
    rank_students,
    semester_trends,
    student_trend,
    top_performers,
    trend_direction,
)


class TestCentralTendency:
    def test_mean(self) -> None:
        assert mean([90, 100, 70, 60, 80, 80]) == 80.0

    def test_median_odd_and_even(self) -> None:
        assert median([3, 1, 2]) == 2
        assert median([4, 1, 3, 2]) == 2.5

    def test_mode_single_and_multimodal(self) -> None:
        assert mode([80, 90, 80, 70]) == [80]
        assert mode([1, 2, 2, 1, 3]) == [1, 2]

    @pytest.mark.parametrize("func", [mean, median, mode])
    def test_empty_input_raises(self, func: object) -> None:
        with pytest.raises(ValueError):
            func([])  # type: ignore[operator]


class TestPercentiles:
    def test_percentile_rank(self) -> None:
        population = [60, 70, 80, 90]
        assert percentile_rank(60, population) == 12.5
        assert percentile_rank(90, population) == 87.5
        assert percentile_rank(100, population) == 100.0

    def test_ties_share_percentile(self) -> None:
        ranks = percentile_ranks({"a": 80, "b": 80, "c": 60})
        assert ranks["a"] == ranks["b"] == pytest.approx(66.667, abs=1e-3)
        assert ranks["c"] == pytest.approx(16.667, abs=1e-3)

    def test_empty_population_raises(self) -> None:
        with pytest.raises(ValueError):
            percentile_rank(50, [])


class TestRanking:
    def test_rank_students_orders_by_average(self, dataset: Dataset) -> None:
        ranked = rank_students(dataset.students.values())
        assert [(r.rank, r.name, r.average) for r in ranked] == [
            (1, "Alice", 95.0),
            (2, "Cara", 80.0),
            (3, "Bob", 65.0),
        ]
        assert ranked[0].percentile == pytest.approx(83.333, abs=1e-3)
        assert ranked[0].courses_taken == 2

    def test_competition_ranking_for_ties(self) -> None:
        students = []
        scores = [("S1", 90.0), ("S2", 90.0), ("S3", 70.0), ("S4", 50.0)]
        for sid, score in scores:
            student = Student(sid, sid, "CS", 1)
            student.add_grade(Grade(sid, "C1", "2024-S1", score))
            students.append(student)
        students.append(Student("S5", "No grades", "CS", 1))
        ranked = rank_students(students)
        assert [(r.student_id, r.rank) for r in ranked] == [
            ("S1", 1), ("S2", 1), ("S3", 3), ("S4", 4),
        ]

    def test_top_performers(self, dataset: Dataset) -> None:
        ranked = rank_students(dataset.students.values())
        assert [r.name for r in top_performers(ranked, 2)] == ["Alice", "Cara"]
        assert len(top_performers(ranked, 10)) == 3
        with pytest.raises(ValueError):
            top_performers(ranked, -1)


class TestTrends:
    def test_semester_trends_with_rolling_average(self) -> None:
        grades = [
            Grade("S1", "C1", "2024-S2", 80.0),
            Grade("S1", "C1", "2023-S1", 60.0),
            Grade("S2", "C1", "2023-S2", 70.0),
            Grade("S2", "C2", "2023-S2", 90.0),
        ]
        trends = semester_trends(grades, window=2)
        assert [t.semester for t in trends] == [
            "2023-S1", "2023-S2", "2024-S2",
        ]
        assert [t.average for t in trends] == [60.0, 80.0, 80.0]
        assert [t.rolling_average for t in trends] == [60.0, 70.0, 80.0]
        assert [t.grade_count for t in trends] == [1, 2, 1]

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            ([70, 75], "improving"),
            ([75, 70], "declining"),
            ([70, 70.5], "stable"),
            ([70], "insufficient data"),
            ([], "insufficient data"),
        ],
    )
    def test_trend_direction(self, values: list[float], expected: str) -> None:
        assert trend_direction(values) == expected

    def test_student_trend(self, dataset: Dataset) -> None:
        alice = student_trend(dataset.students["S1"], window=1)
        assert dict(alice.semester_averages) == {
            "2024-S1": 90.0, "2024-S2": 100.0,
        }
        assert alice.direction == "improving"
        bob = student_trend(dataset.students["S2"], window=1)
        cara = student_trend(dataset.students["S3"], window=1)
        assert bob.direction == "declining"
        assert cara.direction == "stable"

    def test_student_trend_is_smoothed(self, dataset: Dataset) -> None:
        alice = student_trend(dataset.students["S1"], window=2)
        assert alice.rolling_averages == [90.0, 95.0]

    def test_all_grades_flattening(self, dataset: Dataset) -> None:
        assert len(all_grades(dataset.students.values())) == 6
