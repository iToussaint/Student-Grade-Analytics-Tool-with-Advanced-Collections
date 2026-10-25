"""Integration tests for the command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grade_analytics.cli import main

from tests.helpers import HEADER

Capture = pytest.CaptureFixture[str]


def test_cli_writes_report(
    csv_file: Path, tmp_path: Path, capsys: Capture
) -> None:
    output = tmp_path / "out" / "report.json"
    exit_code = main([str(csv_file), "-o", str(output), "--top", "2"])
    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert len(report["top_performers"]) == 2
    printed = capsys.readouterr().out
    assert "STUDENT GRADE ANALYTICS REPORT" in printed
    assert "Report written to" in printed


def test_cli_no_charts(
    csv_file: Path, tmp_path: Path, capsys: Capture
) -> None:
    args = [str(csv_file), "-o", str(tmp_path / "r.json"), "--no-charts"]
    assert main(args) == 0
    assert "Grade Distribution" not in capsys.readouterr().out


def test_cli_missing_file(tmp_path: Path, capsys: Capture) -> None:
    args = [str(tmp_path / "missing.csv"), "-o", str(tmp_path / "r.json")]
    assert main(args) == 1
    assert "Input file not found" in capsys.readouterr().err


def test_cli_file_without_valid_rows(
    tmp_path: Path, capsys: Capture
) -> None:
    path = tmp_path / "empty.csv"
    path.write_text(HEADER, encoding="utf-8")
    assert main([str(path), "-o", str(tmp_path / "r.json")]) == 1
    assert "empty dataset" in capsys.readouterr().err


def test_cli_rejects_non_positive_top(csv_file: Path) -> None:
    with pytest.raises(SystemExit):
        main([str(csv_file), "--top", "0"])


def test_cli_memory_report(
    csv_file: Path, tmp_path: Path, capsys: Capture
) -> None:
    args = [
        str(csv_file), "-o", str(tmp_path / "r.json"),
        "--no-charts", "--memory-report",
    ]
    assert main(args) == 0
    assert "MEMORY USAGE COMPARISON" in capsys.readouterr().out
