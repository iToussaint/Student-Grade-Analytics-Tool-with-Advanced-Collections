"""JSON report construction and text-based terminal charts."""

from grade_analytics.reporting.charts import (
    bar_chart,
    distribution_chart,
    render_summary,
    score_baseline,
    semester_chart,
    top_performers_table,
)
from grade_analytics.reporting.report import (
    CourseSummary,
    GradeReport,
    GroupSummary,
    RankingEntry,
    ReportMetadata,
    SemesterTrendEntry,
    StudentTrendEntry,
    SummaryStatistics,
    build_report,
    build_report_from_dataset,
    summarize_scores,
)

__all__ = [
    "CourseSummary",
    "GradeReport",
    "GroupSummary",
    "RankingEntry",
    "ReportMetadata",
    "SemesterTrendEntry",
    "StudentTrendEntry",
    "SummaryStatistics",
    "bar_chart",
    "build_report",
    "build_report_from_dataset",
    "distribution_chart",
    "render_summary",
    "score_baseline",
    "semester_chart",
    "summarize_scores",
    "top_performers_table",
]
