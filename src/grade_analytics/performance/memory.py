"""Memory usage comparisons between collection approaches.

Measurements use :mod:`tracemalloc`, which reports the memory allocated by
Python while a piece of code runs. Absolute numbers vary with the Python
version and platform; the relative differences are what matter.
"""

from __future__ import annotations

import tracemalloc
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict, List

from grade_analytics.io.files import PathInput, iter_records, load_records
from grade_analytics.models.entities import GradeRecord


@dataclass(frozen=True, slots=True)
class MemoryResult:
    """Peak memory allocated by one approach."""

    approach: str
    peak_bytes: int


@dataclass(frozen=True, slots=True)
class MemoryComparison:
    """A group of approaches solving the same task."""

    task: str
    results: List[MemoryResult]


def measure_peak(func: Callable[[], Any]) -> int:
    """Peak bytes allocated while ``func`` runs (its result is kept alive)."""
    tracemalloc.start()
    try:
        result = func()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    del result
    return peak


@dataclass
class _PlainRecord:
    """Regular dataclass (with a per-instance ``__dict__``) for comparison."""

    student_id: str
    name: str
    major: str
    year: int
    course_code: str
    course_name: str
    credits: int
    semester: str
    score: float


@dataclass(slots=True)
class _SlottedRecord:
    """Dataclass with ``__slots__`` (no per-instance ``__dict__``)."""

    student_id: str
    name: str
    major: str
    year: int
    course_code: str
    course_name: str
    credits: int
    semester: str
    score: float


def _sample_values(index: int) -> Dict[str, Any]:
    """Field values for the ``index``-th synthetic record."""
    return {
        "student_id": f"S{index:05d}",
        "name": f"Student {index}",
        "major": "Computer Science",
        "year": 1 + index % 4,
        "course_code": f"CS{100 + index % 10}",
        "course_name": "Course",
        "credits": 3,
        "semester": "2024-S1",
        "score": float(index % 101),
    }


def compare_record_structures(count: int = 10_000) -> MemoryComparison:
    """Memory needed to hold ``count`` records in different structures."""
    rows = [_sample_values(i) for i in range(count)]
    approaches: Dict[str, Callable[[], Any]] = {
        "dict": lambda: [dict(row) for row in rows],
        "dataclass": lambda: [_PlainRecord(**row) for row in rows],
        "dataclass(slots=True)": lambda: [
            _SlottedRecord(**row) for row in rows
        ],
        "namedtuple": lambda: [GradeRecord(**row) for row in rows],
    }
    return MemoryComparison(
        task=f"Store {count:,} records",
        results=[
            MemoryResult(name, measure_peak(fn))
            for name, fn in approaches.items()
        ],
    )


def compare_rolling_window(
    count: int = 100_000, window: int = 3
) -> MemoryComparison:
    """Keeping a rolling window: a growing list versus ``deque(maxlen)``."""

    def with_list() -> List[float]:
        """Keep every value in a list and average its last ``window``."""
        values: List[float] = []
        for i in range(count):
            values.append(float(i))
            _ = sum(values[-window:]) / min(len(values), window)
        return values

    def with_deque() -> Deque[float]:
        """Keep only the last ``window`` values in a bounded deque."""
        values: Deque[float] = deque(maxlen=window)
        for i in range(count):
            values.append(float(i))
            _ = sum(values) / len(values)
        return values

    return MemoryComparison(
        task=f"Rolling average over {count:,} values (window={window})",
        results=[
            MemoryResult("list (keeps all values)", measure_peak(with_list)),
            MemoryResult("deque(maxlen=window)", measure_peak(with_deque)),
        ],
    )


def compare_file_loading(path: PathInput) -> MemoryComparison:
    """Mean score of a CSV file: load all records vs stream a generator."""

    def with_list() -> float:
        """Load every record into a list before averaging."""
        records: List[GradeRecord] = load_records(path)
        return sum(r.score for r in records) / max(len(records), 1)

    def with_generator() -> float:
        """Average records one at a time as the generator yields them."""
        total = 0.0
        count = 0
        for record in iter_records(path):
            total += record.score
            count += 1
        return total / max(count, 1)

    return MemoryComparison(
        task=f"Mean score of {path}",
        results=[
            MemoryResult("list (load_records)", measure_peak(with_list)),
            MemoryResult(
                "generator (iter_records)", measure_peak(with_generator)
            ),
        ],
    )


def format_comparisons(comparisons: List[MemoryComparison]) -> str:
    """Human-readable table of memory comparisons."""
    lines = ["MEMORY USAGE COMPARISON", "=" * 60]
    for comparison in comparisons:
        lines.append(comparison.task)
        smallest = min(r.peak_bytes for r in comparison.results) or 1
        for result in comparison.results:
            ratio = result.peak_bytes / smallest
            lines.append(
                f"  {result.approach:<28}"
                f"{result.peak_bytes / 1024:>12,.1f} KiB"
                f"{ratio:>8.2f}x"
            )
        lines.append("")
    return "\n".join(lines).rstrip()
