"""Tests for each collection type: Counter, defaultdict, OrderedDict, deque."""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict
from typing import List

import pytest

from grade_analytics.aggregators import (
    Dataset,
    RollingAverage,
    all_grades,
    build_dataset,
    grade_distribution,
    group_by_major,
    group_by_year,
    ordered_distribution,
    scores_by_course,
    scores_by_semester,
)
from grade_analytics.models import GradeRecord


class TestDataset:
    def test_builds_students_and_courses(self, dataset: Dataset) -> None:
        assert set(dataset.students) == {"S1", "S2", "S3"}
        assert set(dataset.courses) == {"C1", "C2"}
        assert dataset.courses["C2"].credits == 4
        assert dataset.record_count == 6
        assert len(dataset.students["S1"].grades) == 2

    def test_accepts_a_generator(self, records: List[GradeRecord]) -> None:
        dataset = build_dataset(record for record in records)
        assert dataset.record_count == len(records)


class TestCounter:
    def test_grade_distribution_counts_letters(self, dataset: Dataset) -> None:
        counts = grade_distribution(all_grades(dataset.students.values()))
        assert isinstance(counts, Counter)
        assert counts == Counter({"A": 2, "B": 2, "C": 1, "D": 1})
        assert counts["F"] == 0

    def test_empty_distribution(self) -> None:
        assert grade_distribution([]) == Counter()


class TestOrderedDict:
    def test_distribution_is_ordered_a_to_f_with_zeros(self) -> None:
        result = ordered_distribution(Counter({"C": 3, "A": 1}))
        assert isinstance(result, OrderedDict)
        assert list(result.items()) == [
            ("A", 1), ("B", 0), ("C", 3), ("D", 0), ("F", 0),
        ]


class TestDefaultDict:
    def test_group_by_major(self, dataset: Dataset) -> None:
        groups = group_by_major(dataset.students.values())
        assert isinstance(groups, defaultdict)
        cs_ids = sorted(s.student_id for s in groups["Computer Science"])
        assert cs_ids == ["S1", "S3"]
        assert [s.student_id for s in groups["Mathematics"]] == ["S2"]
        assert groups["Physics"] == []

    def test_group_by_year(self, dataset: Dataset) -> None:
        groups = group_by_year(dataset.students.values())
        assert sorted(s.student_id for s in groups[1]) == ["S2", "S3"]
        assert [s.student_id for s in groups[2]] == ["S1"]

    def test_scores_by_course_and_semester(self, dataset: Dataset) -> None:
        grades = all_grades(dataset.students.values())
        assert sorted(scores_by_course(grades)["C1"]) == [70.0, 80.0, 90.0]
        by_semester = scores_by_semester(grades)
        assert sorted(by_semester["2024-S2"]) == [60.0, 80.0, 100.0]


class TestRollingAverage:
    def test_window_discards_oldest_values(self) -> None:
        rolling = RollingAverage(window=3)
        results = [rolling.add(v) for v in (10, 20, 30, 40, 50)]
        assert results == pytest.approx([10, 15, 20, 30, 40])
        assert rolling.values == [30, 40, 50]
        assert len(rolling) == 3

    def test_window_size_stays_bounded(self) -> None:
        rolling = RollingAverage(window=2)
        for value in range(1_000):
            rolling.add(float(value))
            assert len(rolling) <= rolling.window
        assert rolling.values == [998.0, 999.0]
        assert rolling.average == pytest.approx(998.5)

    def test_average_is_none_when_empty(self) -> None:
        assert RollingAverage(window=2).average is None

    def test_rejects_invalid_window(self) -> None:
        with pytest.raises(ValueError):
            RollingAverage(window=0)
