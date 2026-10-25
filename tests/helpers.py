"""Shared test data: a tiny dataset whose statistics are easy to verify.

Student averages: Alice 95, Cara 80, Bob 65.
All scores: 90, 100, 70, 60, 80, 80 -> mean 80, median 80, mode 80.
"""

from __future__ import annotations

from pathlib import Path

HEADER = (
    "student_id,name,major,year,course_code,course_name,credits,"
    "semester,score\n"
)
CSV_TEXT = HEADER + """\
S1,Alice,Computer Science,2,C1,Course One,3,2024-S1,90
S1,Alice,Computer Science,2,C2,Course Two,4,2024-S2,100
S2,Bob,Mathematics,1,C1,Course One,3,2024-S1,70
S2,Bob,Mathematics,1,C2,Course Two,4,2024-S2,60
S3,Cara,Computer Science,1,C1,Course One,3,2024-S1,80
S3,Cara,Computer Science,1,C2,Course Two,4,2024-S2,80
"""

SAMPLE_DATA = (
    Path(__file__).resolve().parent.parent / "data" / "sample_grades.csv"
)
