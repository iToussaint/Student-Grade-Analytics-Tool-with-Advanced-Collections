"""Text-based charts for the terminal (standard library only)."""

from __future__ import annotations

from typing import List, Mapping, Sequence

from grade_analytics.report import GradeReport, RankingEntry, SemesterTrendEntry

BAR_CHAR = "#"
DEFAULT_WIDTH = 40


def bar_chart(
    data: Mapping[str, float],
    title: str,
    width: int = DEFAULT_WIDTH,
    value_format: str = "{:g}",
) -> str:
    """Render a horizontal bar chart.

    Bars are scaled relative to the largest value so the longest bar is
    ``width`` characters long. Labels are left-aligned in a common column.

    Args:
        data: Ordered mapping of label to value.
        title: Heading printed above the chart.
        width: Maximum bar length in characters.
        value_format: Format string applied to each value.
    """
    lines: List[str] = [title, "-" * len(title)]
    if not data:
        lines.append("(no data)")
        return "\n".join(lines)

    label_width = max(len(label) for label in data)
    largest = max(data.values())
    for label, value in data.items():
        length = round(width * value / largest) if largest > 0 else 0
        bar = BAR_CHAR * length
        lines.append(f"{label:<{label_width}} | {bar} {value_format.format(value)}")
    return "\n".join(lines)


def distribution_chart(distribution: Mapping[str, int], width: int = DEFAULT_WIDTH) -> str:
    """Bar chart of the letter grade distribution with percentages."""
    total = sum(distribution.values())
    lines = [bar_chart(distribution, "Grade Distribution", width)]
    if total:
        shares = ", ".join(
            f"{letter}: {100 * count / total:.1f}%" for letter, count in distribution.items()
        )
        lines.append(f"Share -> {shares}")
    return "\n".join(lines)


def semester_chart(trends: Sequence[SemesterTrendEntry], width: int = DEFAULT_WIDTH) -> str:
    """Bar chart of the average score per semester, with rolling average."""
    lines = [
        bar_chart(
            {t["semester"]: t["average"] for t in trends},
            "Average Score per Semester",
            width,
            value_format="{:.2f}",
        )
    ]
    if trends:
        rolling = ", ".join(f"{t['semester']}: {t['rolling_average']:.2f}" for t in trends)
        lines.append(f"Rolling average -> {rolling}")
    return "\n".join(lines)


def top_performers_table(entries: Sequence[RankingEntry]) -> str:
    """Fixed-width table of the top-ranked students."""
    header = f"{'Rank':<5}{'ID':<8}{'Name':<22}{'Major':<20}{'Avg':>7}{'Pctl':>8}"
    lines = ["Top Performers", "-" * len(header), header]
    for e in entries:
        lines.append(
            f"{e['rank']:<5}{e['student_id']:<8}{e['name'][:21]:<22}"
            f"{e['major'][:19]:<20}{e['average']:>7.2f}{e['percentile']:>8.1f}"
        )
    return "\n".join(lines)


def render_summary(report: GradeReport, width: int = DEFAULT_WIDTH) -> str:
    """Complete console summary of a report: figures, tables and charts."""
    meta = report["metadata"]
    summary = report["summary"]
    mode_text = ", ".join(f"{value:g}" for value in summary["mode"])
    sections = [
        "=" * 60,
        "STUDENT GRADE ANALYTICS REPORT",
        "=" * 60,
        f"Source file : {meta['source_file']}",
        f"Records     : {meta['total_records']}",
        f"Students    : {meta['total_students']}",
        f"Courses     : {meta['total_courses']}",
        f"Semesters   : {', '.join(meta['semesters'])}",
        "",
        f"Mean {summary['mean']:.2f} | Median {summary['median']:.2f} | "
        f"Mode {mode_text} | Min {summary['minimum']:g} | Max {summary['maximum']:g}",
        "",
        distribution_chart(report["grade_distribution"], width),
        "",
        bar_chart(
            {major: group["average"] for major, group in report["by_major"].items()},
            "Average Score by Major",
            width,
            value_format="{:.2f}",
        ),
        "",
        bar_chart(
            {f"Year {year}": group["average"] for year, group in report["by_year"].items()},
            "Average Score by Year",
            width,
            value_format="{:.2f}",
        ),
        "",
        semester_chart(report["semester_trends"], width),
        "",
        top_performers_table(report["top_performers"]),
        "",
        bar_chart(report["trend_summary"], "Student Trends", width),
    ]
    return "\n".join(sections)
