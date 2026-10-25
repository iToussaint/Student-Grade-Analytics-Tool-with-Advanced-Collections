"""Student Grade Analytics Tool.

Processes student grade records from CSV files, computes statistics with
Python's advanced collections and produces JSON reports.

Subpackages:
    models       Domain dataclasses and the ``GradeRecord`` namedtuple.
    io           Streaming CSV reader and JSON writer.
    analysis     Collection-based aggregators and statistics.
    reporting    JSON report builder and terminal charts.
    performance  Memory usage comparisons.
"""

__version__ = "1.0.0"
