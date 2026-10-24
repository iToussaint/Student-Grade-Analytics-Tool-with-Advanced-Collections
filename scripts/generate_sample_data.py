"""Generate a reproducible CSV of student grades.

Usage:
    python scripts/generate_sample_data.py data/sample_grades.csv --students 30
    python scripts/generate_sample_data.py data/large_grades.csv --students 20000

Each student has a base ability and a personal trend, so the data contains
realistic distributions, rankings and semester-to-semester trends.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple

SEMESTERS: List[str] = ["2023-S1", "2023-S2", "2024-S1", "2024-S2"]

FIRST_NAMES = [
    "Amara", "Kwame", "Fatima", "Yaw", "Esi", "Chidi", "Nadia", "Kofi",
    "Zainab", "Tunde", "Abena", "Ibrahim", "Ama", "Sekou", "Aisha", "Jabari",
    "Efua", "Malik", "Naledi", "Obinna",
]
LAST_NAMES = [
    "Mensah", "Okafor", "Diallo", "Asante", "Boateng", "Nwosu", "Traore",
    "Owusu", "Adeyemi", "Kamara", "Appiah", "Bello", "Mutua", "Ndlovu",
]

# Courses per major: (code, name, credits).
COURSES: Dict[str, List[Tuple[str, str, int]]] = {
    "Computer Science": [
        ("CS101", "Introduction to Programming", 4),
        ("CS201", "Data Structures", 4),
        ("CS301", "Algorithms", 3),
        ("CS310", "Databases", 3),
    ],
    "Mathematics": [
        ("MA101", "Calculus I", 4),
        ("MA201", "Linear Algebra", 3),
        ("MA301", "Probability Theory", 3),
        ("MA310", "Numerical Methods", 3),
    ],
    "Business": [
        ("BU101", "Principles of Management", 3),
        ("BU201", "Financial Accounting", 3),
        ("BU301", "Marketing Strategy", 3),
        ("BU310", "Business Analytics", 3),
    ],
}
SHARED_COURSES: List[Tuple[str, str, int]] = [
    ("GE101", "Academic Writing", 2),
    ("GE201", "Statistics for Everyone", 3),
]

FIELDNAMES = [
    "student_id", "name", "major", "year", "course_code",
    "course_name", "credits", "semester", "score",
]


def generate_rows(students: int, seed: int) -> List[Dict[str, object]]:
    """Create grade rows for ``students`` students."""
    rng = random.Random(seed)
    rows: List[Dict[str, object]] = []
    majors = list(COURSES)
    for index in range(1, students + 1):
        student_id = f"S{index:04d}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        major = majors[(index - 1) % len(majors)]
        year = rng.randint(1, 4)
        # First-year students have only completed the two latest semesters.
        semesters = SEMESTERS[-2:] if year == 1 else SEMESTERS
        ability = rng.gauss(74, 9)
        trend = rng.gauss(0, 2.5)
        catalogue = COURSES[major] + SHARED_COURSES
        for offset, semester in enumerate(semesters):
            for code, course_name, credits in rng.sample(catalogue, 3):
                score = ability + trend * offset + rng.gauss(0, 6)
                rows.append(
                    {
                        "student_id": student_id,
                        "name": name,
                        "major": major,
                        "year": year,
                        "course_code": code,
                        "course_name": course_name,
                        "credits": credits,
                        "semester": semester,
                        "score": round(min(100.0, max(0.0, score))),
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sample grade data.")
    parser.add_argument("output", type=Path, help="CSV file to create")
    parser.add_argument("--students", type=int, default=30, help="number of students")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    args = parser.parse_args()

    rows = generate_rows(args.students, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows for {args.students} students to {args.output}")


if __name__ == "__main__":
    main()
