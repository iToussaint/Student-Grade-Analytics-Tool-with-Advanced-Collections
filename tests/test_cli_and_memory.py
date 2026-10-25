"""Tests for the command-line interface and memory comparisons."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grade_analytics.cli import main
from grade_analytics.memory import (
    compare_file_loading,
    compare_record_structures,
    compare_rolling_window,
    format_comparisons,
    measure_peak,
)


def test_cli_writes_report(csv_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "out" / "report.json"
    exit_code = main([str(csv_file), "-o", str(output), "--top", "2"])
    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert len(report["top_performers"]) == 2
    printed = capsys.readouterr().out
    assert "STUDENT GRADE ANALYTICS REPORT" in printed
    assert "Report written to" in printed


def test_cli_no_charts(csv_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(csv_file), "-o", str(tmp_path / "r.json"), "--no-charts"]) == 0
    assert "Grade Distribution" not in capsys.readouterr().out


def test_cli_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "missing.csv"), "-o", str(tmp_path / "r.json")]) == 1
    assert "Input file not found" in capsys.readouterr().err


def test_cli_file_without_valid_rows(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "empty.csv"
    path.write_text(
        "student_id,name,major,year,course_code,course_name,credits,semester,score\n",
        encoding="utf-8",
    )
    assert main([str(path), "-o", str(tmp_path / "r.json")]) == 1
    assert "empty dataset" in capsys.readouterr().err


def test_cli_rejects_non_positive_top(csv_file: Path) -> None:
    with pytest.raises(SystemExit):
        main([str(csv_file), "--top", "0"])


def test_cli_memory_report(csv_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(csv_file), "-o", str(tmp_path / "r.json"), "--no-charts", "--memory-report"]) == 0
    assert "MEMORY USAGE COMPARISON" in capsys.readouterr().out


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


def test_generator_uses_less_memory_than_list(csv_file: Path) -> None:
    comparison = compare_file_loading(csv_file)
    assert len(comparison.results) == 2
    text = format_comparisons([comparison])
    assert "generator (iter_records)" in text
