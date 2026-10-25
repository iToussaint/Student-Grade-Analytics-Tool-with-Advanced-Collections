# Student Grade Analytics Tool with Advanced Collections

A command-line tool that reads student grade records from a CSV file, computes
statistics (averages, distributions, rankings, percentiles, semester trends)
and writes a structured JSON report. It also prints text charts in the
terminal.

It is built on Python's standard library: `Counter`, `defaultdict`,
`OrderedDict`, `deque`, `dataclasses`, `namedtuple`, `TypedDict` and full type
hints, checked with `mypy --strict`.

---

## Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Input Format](#input-format)
6. [Sample Output](#sample-output)
7. [JSON Report Examples](#json-report-examples)
8. [Design: Collections and Data Models](#design-collections-and-data-models)
9. [Collection Performance Notes](#collection-performance-notes)
10. [Testing and Type Checking](#testing-and-type-checking)
11. [Screenshot](#screenshot)

---

## Features

- Reads CSV files with `csv.DictReader` inside a `with` block, using `pathlib`.
- Streams records through a **generator**, so large files are never fully
  loaded into memory.
- Validates each row. Invalid rows are logged and skipped, and missing,
  unreadable or malformed files give a clear error message.
- Statistics: mean, median, mode (via `Counter`), min/max, percentile ranks.
- Competition ranking ("1224") of students by average, plus top performers.
- Grade distribution (A–F) overall, per major, per year and per course.
- Semester trends with a `deque`-backed rolling average, and a trend label
  for each student (improving / declining / stable).
- Pretty-printed JSON report, with its structure defined by `TypedDict`.
- Text bar charts and tables in the terminal (no third-party dependencies).
- Optional memory-usage comparison of different collection approaches.

## Project Structure

```
.
├── grade_analytics/
│   ├── __init__.py
│   ├── __main__.py        # python -m grade_analytics
│   ├── cli.py             # argparse command-line interface
│   ├── models.py          # Student, Course, Grade dataclasses; GradeRecord namedtuple
│   ├── aggregators.py     # Counter / defaultdict / OrderedDict / deque helpers
│   ├── file_io.py         # CSV reader (generator) and JSON writer
│   ├── stats.py           # mean, median, mode, percentiles, ranking, trends
│   ├── report.py          # TypedDict report schema and report builder
│   ├── visualization.py   # text charts and tables
│   └── memory.py          # tracemalloc-based memory comparisons
├── scripts/
│   └── generate_sample_data.py
├── data/
│   └── sample_grades.csv  # 30 students, 312 grade records
├── tests/                 # pytest suite
├── pyproject.toml         # mypy and pytest configuration
└── requirements.txt
```

## Setup

Requires **Python 3.11+**.

```bash
git clone https://github.com/iToussaint/Student-Grade-Analytics-Tool-with-Advanced-Collections.git
cd Student-Grade-Analytics-Tool-with-Advanced-Collections

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

The tool itself uses only the standard library. `pytest` and `mypy` are
needed only for development.

## Usage

```bash
python -m grade_analytics data/sample_grades.csv
```

| Option | Default | Description |
|---|---|---|
| `input` | – | CSV file with one row per grade |
| `-o`, `--output` | `reports/grade_report.json` | Where the JSON report is written |
| `-t`, `--top` | `5` | Number of top performers to list |
| `-w`, `--window` | `3` | Rolling-average window, in semesters |
| `--no-charts` | off | Skip the console summary and charts |
| `--memory-report` | off | Print memory comparisons of collection approaches |

Examples:

```bash
# Top 10 students, 2-semester rolling window, custom output path
python -m grade_analytics data/sample_grades.csv -t 10 -w 2 -o reports/cs.json

# Only write the JSON report and show the memory comparison
python -m grade_analytics data/sample_grades.csv --no-charts --memory-report
```

The command exits with code `0` on success and `1` on error, for example:

```
$ python -m grade_analytics missing.csv
Error: Input file not found: missing.csv
```

### Generating data

```bash
# Re-create the committed sample (seeded, so the output is reproducible)
python scripts/generate_sample_data.py data/sample_grades.csv --students 30

# Large dataset for performance testing (~210,000 rows, ~15 MB; git-ignored)
python scripts/generate_sample_data.py data/large_grades.csv --students 20000
```

## Input Format

Each CSV row is **one grade**: one student, one course, one semester.

| Column | Type | Example |
|---|---|---|
| `student_id` | text | `S0001` |
| `name` | text | `Yaw Mensah` |
| `major` | text | `Computer Science` |
| `year` | integer ≥ 1 | `3` |
| `course_code` | text | `CS101` |
| `course_name` | text | `Introduction to Programming` |
| `credits` | integer ≥ 1 | `4` |
| `semester` | text, sortable (`YYYY-Sn`) | `2023-S1` |
| `score` | number 0–100 | `73` |

```csv
student_id,name,major,year,course_code,course_name,credits,semester,score
S0001,Yaw Mensah,Computer Science,3,CS101,Introduction to Programming,4,2023-S1,73
S0001,Yaw Mensah,Computer Science,3,GE101,Academic Writing,2,2023-S1,73
S0001,Yaw Mensah,Computer Science,3,GE201,Statistics for Everyone,3,2023-S1,78
```

Letter grades: **A** ≥ 90, **B** ≥ 80, **C** ≥ 70, **D** ≥ 60, **F** < 60.

Rows with missing fields, non-numeric values or scores outside 0–100 are
skipped, with a warning such as:

```
WARNING: Skipping data/grades.csv line 3: Invalid score: 'abc'
```

## Sample Output

`python -m grade_analytics data/sample_grades.csv`

```
============================================================
STUDENT GRADE ANALYTICS REPORT
============================================================
Source file : sample_grades.csv
Records     : 312
Students    : 30
Courses     : 14
Semesters   : 2023-S1, 2023-S2, 2024-S1, 2024-S2

Mean 73.43 | Median 73.00 | Mode 71 | Min 44 | Max 100

Grade Distribution
------------------
A | ############# 31
B | ########################## 62
C | ######################################## 96
D | #################################### 86
F | ############### 37
Share -> A: 9.9%, B: 19.9%, C: 30.8%, D: 27.6%, F: 11.9%

Average Score by Major
----------------------
Business         | ###################################### 72.76
Computer Science | ######################################## 75.95
Mathematics      | ###################################### 71.63

Average Score by Year
---------------------
Year 1 | ######################################## 78.06
Year 2 | #################################### 70.14
Year 3 | ################################### 68.27
Year 4 | ####################################### 75.26

Average Score per Semester
--------------------------
2023-S1 | ######################################## 73.29
2023-S2 | ####################################### 72.79
2024-S1 | ######################################## 73.84
2024-S2 | ######################################## 73.60
Rolling average -> 2023-S1: 73.29, 2023-S2: 73.04, 2024-S1: 73.31, 2024-S2: 73.41

Top Performers
----------------------------------------------------------------------
Rank ID      Name                  Major                   Avg    Pctl
1    S0026   Sekou Ndlovu          Mathematics           96.33    98.3
2    S0010   Yaw Mensah            Computer Science      93.83    95.0
3    S0022   Malik Owusu           Computer Science      90.75    91.7
4    S0009   Kwame Appiah          Business              88.17    88.3
5    S0015   Esi Traore            Business              85.00    85.0

Student Trends
--------------
declining | ######################################## 15
improving | ########################### 10
stable    | ############# 5

Report written to .../reports/grade_report.json
```

## JSON Report Examples

The report has these top-level sections, always in this order:

| Section | Content |
|---|---|
| `metadata` | Source file, generation time (UTC), counts, semesters |
| `summary` | `count`, `mean`, `median`, `mode` (list, to handle multimodal data), `minimum`, `maximum` |
| `grade_distribution` | Count per letter, always A→F, including zeros |
| `top_performers` | First *N* entries of `rankings` |
| `rankings` | Every student with rank, average, percentile |
| `by_major` / `by_year` | Student count, average, median and distribution per group |
| `courses` | Per-course enrollments, mean, median, mode and distribution |
| `semester_trends` | Average and rolling average per semester |
| `student_trends` | Per-student semester averages, rolling averages and direction |
| `trend_summary` | Number of students improving / declining / stable |

Numbers are rounded to 2 decimal places. Excerpts from
`reports/grade_report.json` generated from the sample data:

```json
{
  "metadata": {
    "source_file": "sample_grades.csv",
    "generated_at": "2026-10-25T13:43:57+00:00",
    "total_records": 312,
    "total_students": 30,
    "total_courses": 14,
    "semesters": ["2023-S1", "2023-S2", "2024-S1", "2024-S2"]
  },
  "summary": {
    "count": 312,
    "mean": 73.43,
    "median": 73.0,
    "mode": [71.0],
    "minimum": 44.0,
    "maximum": 100.0
  },
  "grade_distribution": { "A": 31, "B": 62, "C": 96, "D": 86, "F": 37 },
  "top_performers": [
    {
      "rank": 1,
      "student_id": "S0026",
      "name": "Sekou Ndlovu",
      "major": "Mathematics",
      "year": 4,
      "average": 96.33,
      "percentile": 98.33,
      "courses_taken": 12
    }
  ]
}
```

Group and course sections:

```json
{
  "by_major": {
    "Business": {
      "student_count": 10,
      "average": 72.76,
      "median": 72.0,
      "grade_distribution": { "A": 8, "B": 22, "C": 31, "D": 37, "F": 10 }
    }
  },
  "courses": {
    "BU101": {
      "name": "Principles of Management",
      "credits": 3,
      "enrollments": 13,
      "mean": 74.92,
      "median": 77.0,
      "mode": [61.0, 79.0],
      "grade_distribution": { "A": 2, "B": 2, "C": 4, "D": 5, "F": 0 }
    }
  }
}
```

Trend sections:

```json
{
  "semester_trends": [
    { "semester": "2023-S1", "average": 73.29, "rolling_average": 73.29, "grade_count": 66 },
    { "semester": "2023-S2", "average": 72.79, "rolling_average": 73.04, "grade_count": 66 }
  ],
  "student_trends": [
    {
      "student_id": "S0001",
      "name": "Yaw Mensah",
      "semester_averages": { "2023-S1": 74.67, "2023-S2": 72.67, "2024-S1": 75.67, "2024-S2": 79.67 },
      "rolling_averages": [74.67, 73.67, 74.33, 76.0],
      "direction": "improving"
    }
  ],
  "trend_summary": { "declining": 15, "improving": 10, "stable": 5 }
}
```

## Design: Collections and Data Models

### Data models (`models.py`)

| Type | Kind | Why |
|---|---|---|
| `GradeRecord` | `NamedTuple` | Raw CSV row: immutable, very numerous, tuple-sized in memory |
| `Course` | `@dataclass(frozen=True, slots=True)` | Immutable value object |
| `Grade` | `@dataclass(frozen=True, slots=True)` | Immutable; `letter` is a computed property |
| `Student` | `@dataclass(slots=True)` | Mutable: grades are added while aggregating |

`Student.average` and `Student.best_grade()` return `Optional[...]` (a
student may have no grades). `parse_score` accepts
`Union[str, int, float]` and file functions accept `Union[str, Path]`.
The report is described by `TypedDict` classes (`GradeReport`,
`SummaryStatistics`, `RankingEntry`, ...), so mypy checks every key.

### Collections

| Collection | Where | Purpose |
|---|---|---|
| `Counter` | `grade_distribution`, `mode`, `trend_summary` | Count letters, values and trend labels in one pass; `most_common()` for ordering |
| `defaultdict(list)` | `group_by_major`, `group_by_year`, `scores_by_course`, `scores_by_semester` | Group items without checking whether a key exists |
| `defaultdict(Counter)` | per-course distributions | Nested counting in a single pass |
| `OrderedDict` | distributions, `by_major`, `by_year`, `courses`, `semester_averages` | Explicit, stable ordering (A→F, sorted keys, chronological) in the JSON |
| `deque(maxlen=n)` | `RollingAverage` | Fixed-size window: O(1) append, the oldest value drops off automatically |

### Statistics

- **Mean / median**: implemented directly; median sorts once (O(n log n)).
- **Mode**: `Counter` frequencies; *all* values tied for highest frequency
  are returned.
- **Percentile rank**: `100 × (below + 0.5 × equal) / n`. The population is
  sorted once and each lookup uses `bisect` (O(log n)), so ranking *n*
  students costs O(n log n) instead of O(n²).
- **Ranking**: standard competition ranking. Equal averages share a rank
  (1, 1, 3, …) and ties are listed by student id.
- **Trends**: semester identifiers sort chronologically. Each student's
  semester averages are smoothed with the rolling average, and the trend is
  *improving* / *declining* if the smoothed series moves by more than
  1 point from first to last semester, otherwise *stable*.

## Collection Performance Notes

Run `python -m grade_analytics data/sample_grades.csv --memory-report`.
The figures below were measured with `tracemalloc` on Python 3.14 (Windows,
64-bit). Absolute values vary by platform; the ratios are what matter.

```
MEMORY USAGE COMPARISON
============================================================
Store 10,000 records
  dict                             2,739.4 KiB    2.49x
  dataclass                        1,569.7 KiB    1.43x
  dataclass(slots=True)            1,099.1 KiB    1.00x
  namedtuple                       1,333.4 KiB    1.21x

Rolling average over 100,000 values (window=3)
  list (keeps all values)          3,123.6 KiB 2351.91x
  deque(maxlen=window)                 1.3 KiB    1.00x

Mean score of data\large_grades.csv
  list (load_records)             95,654.9 KiB  554.89x
  generator (iter_records)           172.4 KiB    1.00x
```

Key takeaways:

1. **Per-record structure.** A `dict` per row costs about 2.5× more than a
   slotted dataclass, because each instance carries its own hash table.
   A regular dataclass also carries a `__dict__`. `slots=True` removes it,
   and a `namedtuple` stores fields as a tuple. That is why `GradeRecord` is
   a `namedtuple` and the dataclasses use `slots=True`.
2. **Rolling windows.** A `deque(maxlen=n)` uses constant memory no matter
   how many values pass through. A list that keeps every value grows
   linearly. `deque` also makes dropping the oldest value O(1), where
   `list.pop(0)` is O(n).
3. **Generators for large files.** Loading the 210,000-row file into a list
   peaks at ~93 MiB. Streaming it with the `iter_records` generator keeps
   peak memory at ~170 KiB, because only one row exists at a time. The CLI
   passes the generator straight into `build_dataset`, which consumes it in a
   single pass.
4. **Aggregation still needs memory.** Students and their grades must be
   kept to compute medians, rankings and trends. A full report on the
   210,000-row file peaked at ~95 MiB and took ~4 s end to end. The savings
   come from never holding the raw CSV rows *as well as* the aggregated
   objects.
5. **Algorithmic choices.** `defaultdict` / `Counter` group and count in one
   O(n) pass. Percentiles use one sort plus `bisect`. The rolling average
   keeps a running total instead of re-summing the window.

## Testing and Type Checking

```bash
python -m pytest          # 95 tests
python -m mypy            # strict mode: grade_analytics, scripts, tests
```

The test suite covers:

- **Each collection type**: `Counter`, `defaultdict`, `OrderedDict` and
  `deque` (`tests/test_aggregators.py`).
- **Models**: letter boundaries, `Union` score parsing, `Optional` results,
  immutability and `__slots__` (`tests/test_models.py`).
- **File I/O**: generator behaviour, missing file, directory, permission
  errors, missing columns, invalid rows, JSON writing (`tests/test_file_io.py`).
- **Calculations**: mean, median, multimodal mode, percentiles, tie ranking,
  rolling averages, trends (`tests/test_stats.py`).
- **Report**: every section checked against a small hand-computed dataset,
  plus an end-to-end run on `data/sample_grades.csv` (`tests/test_report.py`).
- **CLI and memory**: exit codes, options, and the expected memory ordering
  of the compared structures (`tests/test_cli_and_memory.py`).

## Screenshot

![Tool execution](docs/tool-execution.png)
