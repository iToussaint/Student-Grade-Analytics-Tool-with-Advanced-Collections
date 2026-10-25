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
    "bar_chart",
    "distribution_chart",
    "render_summary",
    "score_baseline",
    "semester_chart",
    "top_performers_table",
    "CourseSummary",
    "GradeReport",
    "GroupSummary",
    "RankingEntry",
    "ReportMetadata",
    "SemesterTrendEntry",
    "StudentTrendEntry",
    "SummaryStatistics",
    "build_report",
    "build_report_from_dataset",
    "summarize_scores",
]
