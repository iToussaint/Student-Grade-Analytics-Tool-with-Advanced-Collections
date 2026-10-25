"""Tests for the memory usage comparisons."""

from __future__ import annotations

from pathlib import Path

from grade_analytics.performance.memory import (
    compare_file_loading,
    compare_record_structures,
    compare_rolling_window,
    format_comparisons,
    measure_peak,
)

from tests.helpers import HEADER


def test_measure_peak_detects_allocation() -> None:
    small = measure_peak(lambda: [0] * 10)
    large = measure_peak(lambda: [0] * 100_000)
    assert large > small


def test_slots_and_namedtuple_use_less_memory_than_dict() -> None:
    comparison = compare_record_structures(count=2_000)
    peaks = {r.approach: r.peak_bytes for r in comparison.results}
    assert peaks["dataclass(slots=True)"] < peaks["dict"]
    assert peaks["namedtuple"] < peaks["dict"]


def test_deque_window_uses_less_memory_than_list() -> None:
    comparison = compare_rolling_window(count=20_000, window=3)
    peaks = {r.approach: r.peak_bytes for r in comparison.results}
    assert peaks["deque(maxlen=window)"] < peaks["list (keeps all values)"]


def test_generator_uses_less_memory_than_list(tmp_path: Path) -> None:
    path = tmp_path / "many.csv"
    rows = "".join(
        f"S{i},Student {i},CS,1,C1,Course,3,2024-S1,{i % 101}\n"
        for i in range(2_000)
    )
    path.write_text(HEADER + rows, encoding="utf-8")

    comparison = compare_file_loading(path)
    peaks = {r.approach: r.peak_bytes for r in comparison.results}
    assert peaks["generator (iter_records)"] < peaks["list (load_records)"]
    assert "generator (iter_records)" in format_comparisons([comparison])
