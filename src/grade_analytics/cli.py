"""Command-line interface for the grade analytics tool."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grade_analytics.io.files import DataFileError, iter_records, write_json
from grade_analytics.performance.memory import (
    compare_file_loading,
    compare_record_structures,
    compare_rolling_window,
    format_comparisons,
)
from grade_analytics.reporting.charts import render_summary
from grade_analytics.reporting.report import build_report

DEFAULT_OUTPUT = Path("reports") / "grade_report.json"


def _positive_int(value: str) -> int:
    """Argparse type that accepts only integers greater than zero."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value}")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="grade_analytics",
        description=("Analyse student grades from a CSV file and write a JSON report."),
    )
    parser.add_argument("input", type=Path, help="CSV file with one row per grade")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"destination of the JSON report (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-t",
        "--top",
        type=_positive_int,
        default=5,
        help="number of top performers to list (default: 5)",
    )
    parser.add_argument(
        "-w",
        "--window",
        type=_positive_int,
        default=3,
        help="rolling average window in semesters (default: 3)",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="do not print the console summary and charts",
    )
    parser.add_argument(
        "--memory-report",
        action="store_true",
        help="also print memory usage comparisons of collection approaches",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the tool and return a process exit code."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    try:
        report = build_report(
            iter_records(args.input),
            source_file=args.input.name,
            top_n=args.top,
            rolling_window=args.window,
        )
        output_path = write_json(report, args.output)
    except (DataFileError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not args.no_charts:
        print(render_summary(report))
        print()
    if args.memory_report:
        comparisons = [
            compare_record_structures(),
            compare_rolling_window(),
            compare_file_loading(args.input),
        ]
        print(format_comparisons(comparisons))
        print()
    print(f"Report written to {output_path}")
    return 0
