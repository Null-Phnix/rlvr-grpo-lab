from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from rlvr_lab.eval_metrics import score_completion, summarize_records
from rlvr_lab.postprocess import postprocess_completion
from rlvr_lab.rewards import (
    FINAL_RE,
    extract_marked_answer,
    has_role_label,
    has_text_after_final_marker,
    normalize_answer,
)

DEFAULT_STOPAWARE_CONFIG = {
    "truncate_after_final_marker": True,
    "stop_sequences": ["\nHuman:", "\nUser:", "\nSystem:", "\nAssistant:", "\nProblem:"],
}

INSTRUCTION_LEAK_PATTERNS = [
    "Do not write anything after it",
    "Solve the math problem",
    "Write the final answer",
    "Problem:",
    "Solution:",
]


def resolve_samples_path(path: Path) -> Path:
    if path.is_dir():
        path = path / "samples.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"samples file does not exist: {path}")
    return path


def load_samples(path: Path) -> list[dict[str, Any]]:
    samples_path = resolve_samples_path(path)
    records: list[dict[str, Any]] = []
    with samples_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def text_after_first_marker(text: str) -> str:
    match = FINAL_RE.search(text)
    if not match:
        return ""
    return text[match.end() :]


def has_instruction_leak(text: str) -> bool:
    tail = text_after_first_marker(text)
    return any(pattern in tail for pattern in INSTRUCTION_LEAK_PATTERNS)


def score_stopaware_record(
    record: Mapping[str, Any],
    *,
    postprocess_config: Mapping[str, Any],
) -> dict[str, Any]:
    return score_completion(
        prompt=str(record.get("prompt", "")),
        completion=postprocess_completion(str(record.get("completion", "")), postprocess_config),
        ground_truth=str(record.get("ground_truth", "")),
        index=int(record.get("index", 0)),
    )


def analyze_records(
    records: Iterable[Mapping[str, Any]],
    *,
    postprocess_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    original_records = [dict(record) for record in records]
    stopaware_config = postprocess_config or DEFAULT_STOPAWARE_CONFIG
    stopaware_records = [
        score_stopaware_record(record, postprocess_config=stopaware_config)
        for record in original_records
    ]

    total = len(original_records)
    marked_count = 0
    marked_correct_count = 0
    marked_correct_trailing_count = 0
    role_leak_count = 0
    instruction_leak_count = 0
    stopaware_final_line_wins = 0
    stopaware_exact_wins = 0
    stopaware_exact_losses = 0

    for original, stopaware in zip(original_records, stopaware_records, strict=True):
        completion = str(original.get("completion", ""))
        marked_answer = normalize_answer(extract_marked_answer(completion))
        expected = normalize_answer(str(original.get("ground_truth", "")))
        marked_correct = (
            marked_answer is not None and expected is not None and marked_answer == expected
        )

        marked_count += int(marked_answer is not None)
        marked_correct_count += int(marked_correct)
        marked_correct_trailing_count += int(
            marked_correct and has_text_after_final_marker(completion)
        )
        role_leak_count += int(has_role_label(completion))
        instruction_leak_count += int(has_instruction_leak(completion))
        stopaware_final_line_wins += int(
            not original.get("final_line_is_answer", False)
            and stopaware["final_line_is_answer"]
        )
        stopaware_exact_wins += int(
            not original.get("exact_correct", False) and stopaware["exact_correct"]
        )
        stopaware_exact_losses += int(
            original.get("exact_correct", False) and not stopaware["exact_correct"]
        )

    original_summary = summarize_records(original_records)
    stopaware_summary = summarize_records(stopaware_records)

    def rate(count: int) -> float:
        return count / total if total else 0.0

    return {
        "num_examples": total,
        "original": original_summary,
        "stopaware": stopaware_summary,
        "marked_answer_count": marked_count,
        "marked_answer_rate": rate(marked_count),
        "marked_answer_correct_count": marked_correct_count,
        "marked_answer_correct_rate": rate(marked_correct_count),
        "marked_correct_with_trailing_count": marked_correct_trailing_count,
        "marked_correct_with_trailing_rate": rate(marked_correct_trailing_count),
        "role_leak_count": role_leak_count,
        "role_leak_rate": rate(role_leak_count),
        "instruction_leak_after_marker_count": instruction_leak_count,
        "instruction_leak_after_marker_rate": rate(instruction_leak_count),
        "stopaware_final_line_wins": stopaware_final_line_wins,
        "stopaware_exact_wins": stopaware_exact_wins,
        "stopaware_exact_losses": stopaware_exact_losses,
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def render_analysis(summary: dict[str, Any]) -> None:
    table = Table(title="Sample Failure Analysis")
    table.add_column("Metric")
    table.add_column("Value")

    rows = [
        ("num_examples", summary["num_examples"]),
        ("original_exact", summary["original"]["exact_correct"]),
        ("original_final_line", summary["original"]["final_line_format_count"]),
        ("original_trailing", summary["original"]["trailing_text_count"]),
        ("stopaware_exact", summary["stopaware"]["exact_correct"]),
        ("stopaware_final_line", summary["stopaware"]["final_line_format_count"]),
        ("stopaware_trailing", summary["stopaware"]["trailing_text_count"]),
        ("marked_answer_correct", summary["marked_answer_correct_count"]),
        ("marked_correct_with_trailing", summary["marked_correct_with_trailing_count"]),
        ("role_leak", summary["role_leak_count"]),
        ("instruction_leak_after_marker", summary["instruction_leak_after_marker_count"]),
        ("stopaware_final_line_wins", summary["stopaware_final_line_wins"]),
        ("stopaware_exact_wins", summary["stopaware_exact_wins"]),
        ("stopaware_exact_losses", summary["stopaware_exact_losses"]),
    ]
    for key, value in rows:
        table.add_row(key, str(value))

    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("samples", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = analyze_records(load_samples(args.samples))
    render_analysis(summary)
    if args.output:
        write_summary(args.output, summary)


if __name__ == "__main__":
    main()
