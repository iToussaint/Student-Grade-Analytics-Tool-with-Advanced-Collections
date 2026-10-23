"""CSV input and JSON output using context managers and ``pathlib``.

The CSV reader is a generator: rows are validated and yielded one at a
time, so arbitrarily large files can be processed without holding every
raw row in memory.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Union

from grade_analytics.models import GradeRecord, parse_score

logger = logging.getLogger(__name__)

# Paths may be given as plain strings (e.g. from the CLI) or as Path objects.
PathInput = Union[str, Path]

REQUIRED_COLUMNS: List[str] = [
    "student_id",
    "name",
    "major",
    "year",
    "course_code",
    "course_name",
    "credits",
    "semester",
    "score",
]


class DataFileError(Exception):
    """Raised when an input or output file cannot be used."""


def _to_path(path: PathInput) -> Path:
    return Path(path).expanduser()


def parse_row(row: Mapping[str, str]) -> GradeRecord:
    """Validate one CSV row and convert it into a ``GradeRecord``.

    Raises:
        ValueError: If a field is missing, empty or has an invalid value.
    """
    values: Dict[str, str] = {}
    for column in REQUIRED_COLUMNS:
        value = (row.get(column) or "").strip()
        if not value:
            raise ValueError(f"Missing value for '{column}'")
        values[column] = value

    try:
        year = int(values["year"])
        credits = int(values["credits"])
    except ValueError as exc:
        raise ValueError(f"Invalid integer field: {exc}") from exc
    if year < 1:
        raise ValueError(f"Invalid year: {year}")
    if credits < 1:
        raise ValueError(f"Invalid credits: {credits}")

    return GradeRecord(
        student_id=values["student_id"],
        name=values["name"],
        major=values["major"],
        year=year,
        course_code=values["course_code"],
        course_name=values["course_name"],
        credits=credits,
        semester=values["semester"],
        score=parse_score(values["score"]),
    )


def iter_records(path: PathInput) -> Iterator[GradeRecord]:
    """Lazily read and validate grade records from a CSV file.

    Invalid rows are logged and skipped so a single bad line does not stop
    the whole analysis.

    Args:
        path: Location of the CSV file.

    Yields:
        One ``GradeRecord`` per valid row.

    Raises:
        DataFileError: If the file is missing, unreadable, not a file, or
            lacks required columns.
    """
    csv_path = _to_path(path)
    # Windows reports directories as PermissionError, so check explicitly.
    if csv_path.is_dir():
        raise DataFileError(f"Expected a file but found a directory: {csv_path}")
    try:
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise DataFileError(
                    f"{csv_path} is missing required columns: {', '.join(missing)}"
                )
            for line_number, row in enumerate(reader, start=2):
                try:
                    yield parse_row(row)
                except ValueError as exc:
                    logger.warning("Skipping %s line %d: %s", csv_path, line_number, exc)
    except FileNotFoundError as exc:
        raise DataFileError(f"Input file not found: {csv_path}") from exc
    except PermissionError as exc:
        raise DataFileError(f"Permission denied reading: {csv_path}") from exc
    except UnicodeDecodeError as exc:
        raise DataFileError(f"{csv_path} is not a valid UTF-8 text file") from exc


def load_records(path: PathInput) -> List[GradeRecord]:
    """Read every valid record from a CSV file into a list."""
    return list(iter_records(path))


def write_json(data: Mapping[str, Any], path: PathInput, indent: int = 2) -> Path:
    """Write a JSON document, creating parent directories if needed.

    Args:
        data: JSON-serialisable mapping (e.g. a report).
        path: Destination file.
        indent: Indentation used for pretty-printing.

    Returns:
        The resolved destination path.

    Raises:
        DataFileError: If the file cannot be written.
    """
    json_path = _to_path(path)
    if json_path.is_dir():
        raise DataFileError(f"Cannot write report, {json_path} is a directory")
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=indent, ensure_ascii=False)
            handle.write("\n")
    except PermissionError as exc:
        raise DataFileError(f"Permission denied writing: {json_path}") from exc
    except OSError as exc:
        raise DataFileError(f"Could not write {json_path}: {exc}") from exc
    return json_path.resolve()

