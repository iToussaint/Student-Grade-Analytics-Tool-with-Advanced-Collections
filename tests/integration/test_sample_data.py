"""End-to-end tests on the committed sample dataset."""

from __future__ import annotations

from grade_analytics.io.files import iter_records
from grade_analytics.reporting.report import build_report

from tests.helpers import SAMPLE_DATA


def test_sample_data_report() -> None:
    """End-to-end run on the committed sample CSV, streamed lazily."""
    report = build_report(
        iter_records(SAMPLE_DATA), source_file=SAMPLE_DATA.name
    )
    meta = report["metadata"]
    assert meta["total_students"] == 30
    assert meta["total_records"] == sum(report["grade_distribution"].values())
    assert len(report["rankings"]) == 30
    assert len(report["top_performers"]) == 5
    averages = [e["average"] for e in report["rankings"]]
    assert averages == sorted(averages, reverse=True)
    assert all(0 <= e["percentile"] <= 100 for e in report["rankings"])
