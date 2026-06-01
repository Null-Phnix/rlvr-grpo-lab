from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from rlvr_lab.postprocess import postprocess_completion
from rlvr_lab.rewards import (
    extract_marked_answer,
    normalize_answer,
)

DEFAULT_BOUNDARY_CONFIG = {
    "truncate_after_final_marker": True,
    "stop_sequences": ["\nHuman:", "\nUser:", "\nSystem:", "\nAssistant:", "\nProblem:"],
}


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


def marked_answer_is_correct(record: Mapping[str, Any]) -> bool:
    predicted = normalize_answer(extract_marked_answer(str(record.get("completion", ""))))
    expected = normalize_answer(str(record.get("ground_truth", "")))
    return predicted is not None and expected is not None and predicted == expected


def make_boundary_record(
    record: Mapping[str, Any],
    *,
    postprocess_config: Mapping[str, Any],
) -> dict[str, Any]:
    completion = postprocess_completion(str(record.get("completion", "")), postprocess_config)
    return {
        "prompt": str(record.get("prompt", "")),
        "completion": completion,
        "ground_truth": str(record.get("ground_truth", "")),
        "source_index": int(record.get("index", 0)),
        "source_exact_correct": bool(record.get("exact_correct", False)),
        "source_final_line_is_answer": bool(record.get("final_line_is_answer", False)),
        "source_completion_chars": int(record.get("completion_chars", len(completion))),
    }


def build_boundary_records(
    records: Iterable[Mapping[str, Any]],
    *,
    require_exact: bool = True,
    require_marked_correct: bool = True,
    postprocess_config: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    total = 0
    skipped_not_exact = 0
    skipped_marker_wrong = 0
    skipped_empty = 0
    config = postprocess_config or DEFAULT_BOUNDARY_CONFIG

    for record in records:
        total += 1
        if require_exact and not bool(record.get("exact_correct", False)):
            skipped_not_exact += 1
            continue
        if require_marked_correct and not marked_answer_is_correct(record):
            skipped_marker_wrong += 1
            continue

        boundary_record = make_boundary_record(record, postprocess_config=config)
        if not boundary_record["prompt"].strip() or not boundary_record["completion"].strip():
            skipped_empty += 1
            continue
        selected.append(boundary_record)

    completion_chars = sum(len(record["completion"]) for record in selected)
    summary = {
        "input_count": total,
        "selected_count": len(selected),
        "skipped_not_exact": skipped_not_exact,
        "skipped_marker_wrong": skipped_marker_wrong,
        "skipped_empty": skipped_empty,
        "avg_completion_chars": completion_chars / len(selected) if selected else 0.0,
        "require_exact": require_exact,
        "require_marked_correct": require_marked_correct,
    }
    return selected, summary


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(dict(record), ensure_ascii=False) + "\n")


def write_summary(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(summary), indent=2, sort_keys=True), encoding="utf-8")


def render_summary(summary: Mapping[str, Any]) -> None:
    table = Table(title="Boundary SFT Data")
    table.add_column("Metric")
    table.add_column("Value")
    for key in [
        "input_count",
        "selected_count",
        "skipped_not_exact",
        "skipped_marker_wrong",
        "skipped_empty",
        "avg_completion_chars",
    ]:
        table.add_row(key, str(summary[key]))
    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("samples", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    parser.add_argument("--allow-inexact", action="store_true")
    parser.add_argument("--allow-unmarked-exact", action="store_true")
    args = parser.parse_args()

    records, summary = build_boundary_records(
        load_samples(args.samples),
        require_exact=not args.allow_inexact,
        require_marked_correct=not args.allow_unmarked_exact,
    )
    write_jsonl(args.output, records)
    write_summary(args.summary_output or args.output.with_suffix(".summary.json"), summary)
    render_summary(summary)


if __name__ == "__main__":
    main()
