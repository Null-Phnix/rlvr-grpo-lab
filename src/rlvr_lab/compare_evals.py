from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

METRICS = [
    "exact_accuracy",
    "final_format_rate",
    "missing_answer_rate",
    "avg_completion_chars",
    "exact_correct",
    "final_format_count",
]


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    baseline = load_summary(args.baseline)
    candidate = load_summary(args.candidate)

    table = Table(title="Eval Comparison")
    table.add_column("Metric")
    table.add_column("Baseline")
    table.add_column("Candidate")
    table.add_column("Delta")

    for metric in METRICS:
        base_value = baseline.get(metric)
        candidate_value = candidate.get(metric)
        delta = (
            candidate_value - base_value
            if isinstance(base_value, (int, float))
            and isinstance(candidate_value, (int, float))
            else ""
        )
        table.add_row(metric, fmt(base_value), fmt(candidate_value), fmt(delta))

    Console().print(table)


if __name__ == "__main__":
    main()
