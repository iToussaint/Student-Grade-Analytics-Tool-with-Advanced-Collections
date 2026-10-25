"""Tests for CSV reading and JSON writing."""

from __future__ import annotations

import json
import logging
import types
from pathlib import Path

import pytest

from grade_analytics.file_io import (
    DataFileError,
    iter_records,
    load_records,
    parse_row,
    write_json,
)

HEADER = "student_id,name,major,year,course_code,course_name,credits,semester,score\n"


def test_iter_records_is_a_lazy_generator(csv_file: Path) -> None:
    records = iter_records(csv_file)
    assert isinstance(records, types.GeneratorType)
    first = next(records)
    assert first.student_id == "S1"
    assert first.score == 90.0
    assert first.year == 2 and first.credits == 3


def test_load_records_accepts_str_and_path(csv_file: Path) -> None:
    assert load_records(csv_file) == load_records(str(csv_file))
    assert len(load_records(csv_file)) == 6


def test_missing_file_raises_data_file_error(tmp_path: Path) -> None:
    with pytest.raises(DataFileError, match="not found"):
        load_records(tmp_path / "missing.csv")


def test_directory_raises_data_file_error(tmp_path: Path) -> None:
    with pytest.raises(DataFileError, match="directory"):
        load_records(tmp_path)


def test_permission_error_is_reported(csv_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "open", deny)
    with pytest.raises(DataFileError, match="Permission denied"):
        load_records(csv_file)


def test_missing_columns_are_reported(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("student_id,name\nS1,Alice\n", encoding="utf-8")
    with pytest.raises(DataFileError, match="missing required columns"):
        load_records(path)


def test_invalid_rows_are_skipped_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "mixed.csv"
    path.write_text(
        HEADER
        + "S1,Alice,CS,2,C1,Course,3,2024-S1,90\n"
        + "S2,Bob,CS,2,C1,Course,3,2024-S1,abc\n"
        + "S3,Cara,CS,2,C1,Course,3,2024-S1,150\n"
        + "S4,,CS,2,C1,Course,3,2024-S1,70\n",
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING):
        records = load_records(path)
    assert [r.student_id for r in records] == ["S1"]
    assert len(caplog.records) == 3
    assert "line 3" in caplog.records[0].getMessage()


@pytest.mark.parametrize(
    ("field", "value"),
    [("year", "first"), ("year", "0"), ("credits", "-2"), ("score", "")],
)
def test_parse_row_validation(field: str, value: str) -> None:
    row = {
        "student_id": "S1", "name": "Alice", "major": "CS", "year": "2",
        "course_code": "C1", "course_name": "Course", "credits": "3",
        "semester": "2024-S1", "score": "90",
    }
    row[field] = value
    with pytest.raises(ValueError):
        parse_row(row)


def test_write_json_creates_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "out" / "report.json"
    written = write_json({"b": 1, "a": [1, 2]}, target)
    assert written == target.resolve()
    content = target.read_text(encoding="utf-8")
    assert json.loads(content) == {"b": 1, "a": [1, 2]}
    assert content.index('"b"') < content.index('"a"')  # insertion order kept
    assert content.endswith("\n")


def test_write_json_to_directory_fails(tmp_path: Path) -> None:
    with pytest.raises(DataFileError, match="is a directory"):
        write_json({}, tmp_path)


def test_write_json_permission_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "open", deny)
    with pytest.raises(DataFileError, match="Permission denied"):
        write_json({}, tmp_path / "report.json")
