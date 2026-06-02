from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from rlvr_lab.analyze_samples import load_samples, resolve_samples_path
from rlvr_lab.compare_samples import problem_text, shorten

TAXONOMY_BUCKETS = [
    "correct_clean_contract",
    "correct_with_trailing_text",
    "correct_marker_not_final_line",
    "correct_without_marker",
    "wrong_math_clean_contract",
    "wrong_with_trailing_text",
    "wrong_marker_not_final_line",
    "wrong_missing_marker",
    "wrong_missing_answer",
]


def bool_field(record: Mapping[str, Any], key: str) -> bool:
    return bool(record.get(key, False))


def taxonomy_bucket(record: Mapping[str, Any]) -> str:
    exact = bool_field(record, "exact_correct")
    has_marker = bool_field(record, "has_final_format")
    final_line = bool_field(record, "final_line_is_answer")
    trailing = bool_field(record, "has_trailing_text_after_final")
    extracted_answer = record.get("extracted_answer")

    if exact:
        if trailing:
            return "correct_with_trailing_text"
        if final_line:
            return "correct_clean_contract"
        if has_marker:
            return "correct_marker_not_final_line"
        return "correct_without_marker"

    if extracted_answer is None:
        return "wrong_missing_answer"
    if trailing:
        return "wrong_with_trailing_text"
    if not has_marker:
        return "wrong_missing_marker"
    if final_line:
        return "wrong_math_clean_contract"
    return "wrong_marker_not_final_line"


def example_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "index": record.get("index"),
        "ground_truth": record.get("normalized_ground_truth") or record.get("ground_truth"),
        "extracted_answer": record.get("normalized_answer") or record.get("extracted_answer"),
        "final_line_answer": record.get("normalized_final_line_answer")
        or record.get("final_line_answer"),
        "completion_chars": record.get("completion_chars"),
        "problem": shorten(problem_text(str(record.get("prompt", ""))), 280),
    }


def summarize_taxonomy(
    records: list[Mapping[str, Any]],
    *,
    max_examples_per_bucket: int = 5,
) -> dict[str, Any]:
    total = len(records)
    counts: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        bucket = taxonomy_bucket(record)
        counts[bucket] += 1
        if len(examples[bucket]) < max_examples_per_bucket:
            examples[bucket].append(example_record(record))

    exact_correct = sum(1 for record in records if bool_field(record, "exact_correct"))
    exact_wrong = total - exact_correct
    wrong_contract_clean = counts["wrong_math_clean_contract"]
    wrong_boundary_or_extraction = exact_wrong - wrong_contract_clean

    def rate(count: int) -> float:
        return count / total if total else 0.0

    def wrong_rate(count: int) -> float:
        return count / exact_wrong if exact_wrong else 0.0

    bucket_counts = {bucket: counts[bucket] for bucket in TAXONOMY_BUCKETS}

    return {
        "num_examples": total,
        "exact_correct": exact_correct,
        "exact_wrong": exact_wrong,
        "exact_accuracy": rate(exact_correct),
        "wrong_math_clean_contract_count": wrong_contract_clean,
        "wrong_math_clean_contract_rate": wrong_rate(wrong_contract_clean),
        "wrong_boundary_or_extraction_count": wrong_boundary_or_extraction,
        "wrong_boundary_or_extraction_rate": wrong_rate(wrong_boundary_or_extraction),
        "bucket_counts": bucket_counts,
        "bucket_rates": {bucket: rate(count) for bucket, count in bucket_counts.items()},
        "examples": {bucket: examples.get(bucket, []) for bucket in TAXONOMY_BUCKETS},
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def render_taxonomy(summary: Mapping[str, Any]) -> None:
    table = Table(title="Failure Taxonomy")
    table.add_column("Bucket")
    table.add_column("Count", justify="right")
    table.add_column("Rate", justify="right")

    total = int(summary["num_examples"])
    counts = summary["bucket_counts"]
    for bucket in TAXONOMY_BUCKETS:
        count = int(counts[bucket])
        rate = count / total if total else 0.0
        table.add_row(bucket, str(count), f"{rate:.4f}")

    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("samples", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-examples-per-bucket", type=int, default=5)
    args = parser.parse_args()

    samples_path = resolve_samples_path(args.samples)
    summary = summarize_taxonomy(
        load_samples(samples_path),
        max_examples_per_bucket=args.max_examples_per_bucket,
    )
    render_taxonomy(summary)
    if args.output:
        write_summary(args.output, summary)


if __name__ == "__main__":
    main()
