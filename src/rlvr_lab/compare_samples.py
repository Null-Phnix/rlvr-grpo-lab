from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


def resolve_samples_path(path: Path) -> Path:
    if path.is_dir():
        path = path / "samples.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"samples file does not exist: {path}")
    return path


def load_samples(path: Path) -> dict[int, dict[str, Any]]:
    samples_path = resolve_samples_path(path)
    records: dict[int, dict[str, Any]] = {}
    with samples_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if "index" not in record:
                raise ValueError(f"{samples_path}:{line_number} is missing index")
            records[int(record["index"])] = record
    return records


def answer(record: dict[str, Any]) -> str:
    value = (
        record.get("normalized_final_line_answer")
        or record.get("normalized_answer")
        or record.get("extracted_answer")
        or ""
    )
    return str(value)


def problem_text(prompt: str) -> str:
    text = prompt
    if "Problem:\n" in text:
        text = text.split("Problem:\n", 1)[1]
    if "\n\nSolution:" in text:
        text = text.split("\n\nSolution:", 1)[0]
    return " ".join(text.split())


def shorten(text: str, limit: int) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def compare_records(
    baseline: dict[int, dict[str, Any]],
    candidate: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    indexes = sorted(set(baseline) & set(candidate))
    missing_from_baseline = sorted(set(candidate) - set(baseline))
    missing_from_candidate = sorted(set(baseline) - set(candidate))

    wins = [
        index
        for index in indexes
        if not baseline[index]["exact_correct"] and candidate[index]["exact_correct"]
    ]
    losses = [
        index
        for index in indexes
        if baseline[index]["exact_correct"] and not candidate[index]["exact_correct"]
    ]
    same_correct = [
        index
        for index in indexes
        if baseline[index]["exact_correct"] and candidate[index]["exact_correct"]
    ]
    same_wrong = [
        index
        for index in indexes
        if not baseline[index]["exact_correct"] and not candidate[index]["exact_correct"]
    ]
    final_line_wins = [
        index
        for index in indexes
        if not baseline[index]["final_line_is_answer"] and candidate[index]["final_line_is_answer"]
    ]
    final_line_losses = [
        index
        for index in indexes
        if baseline[index]["final_line_is_answer"] and not candidate[index]["final_line_is_answer"]
    ]

    return {
        "indexes": indexes,
        "missing_from_baseline": missing_from_baseline,
        "missing_from_candidate": missing_from_candidate,
        "baseline_exact": len(same_correct) + len(losses),
        "candidate_exact": len(same_correct) + len(wins),
        "same_correct": same_correct,
        "same_wrong": same_wrong,
        "wins": wins,
        "losses": losses,
        "final_line_wins": final_line_wins,
        "final_line_losses": final_line_losses,
    }


def render_table(comparison: dict[str, Any], *, baseline_label: str, candidate_label: str) -> None:
    total = len(comparison["indexes"])
    table = Table(title="Sample Comparison")
    table.add_column("Metric")
    table.add_column(baseline_label)
    table.add_column(candidate_label)
    table.add_column("Delta")

    table.add_row(
        "exact_correct",
        f"{comparison['baseline_exact']}/{total}",
        f"{comparison['candidate_exact']}/{total}",
        str(comparison["candidate_exact"] - comparison["baseline_exact"]),
    )
    table.add_row("wins", "", str(len(comparison["wins"])), "")
    table.add_row("losses", "", str(len(comparison["losses"])), "")
    table.add_row("same_correct", str(len(comparison["same_correct"])), "", "")
    table.add_row("same_wrong", str(len(comparison["same_wrong"])), "", "")
    table.add_row("final_line_format_wins", "", str(len(comparison["final_line_wins"])), "")
    table.add_row("final_line_format_losses", "", str(len(comparison["final_line_losses"])), "")

    Console().print(table)


def markdown_section(
    *,
    title: str,
    indexes: list[int],
    baseline: dict[int, dict[str, Any]],
    candidate: dict[int, dict[str, Any]],
    baseline_label: str,
    candidate_label: str,
    max_examples: int,
    completion_chars: int,
) -> list[str]:
    lines = [f"## {title}", ""]
    if not indexes:
        lines.extend(["None.", ""])
        return lines

    for index in indexes[:max_examples]:
        baseline_record = baseline[index]
        candidate_record = candidate[index]
        lines.extend(
            [
                f"### Index {index}",
                "",
                f"- ground truth: `{candidate_record.get('normalized_ground_truth', '')}`",
                (
                    f"- {baseline_label} answer: `{answer(baseline_record)}` "
                    f"correct={baseline_record['exact_correct']}"
                ),
                (
                    f"- {candidate_label} answer: `{answer(candidate_record)}` "
                    f"correct={candidate_record['exact_correct']}"
                ),
                f"- problem: {shorten(problem_text(str(candidate_record.get('prompt', ''))), 360)}",
                (
                    f"- {baseline_label} completion: "
                    f"{shorten(str(baseline_record.get('completion', '')), completion_chars)}"
                ),
                (
                    f"- {candidate_label} completion: "
                    f"{shorten(str(candidate_record.get('completion', '')), completion_chars)}"
                ),
                "",
            ]
        )
    if len(indexes) > max_examples:
        lines.extend([f"Skipped {len(indexes) - max_examples} additional examples.", ""])
    return lines


def render_markdown(
    *,
    comparison: dict[str, Any],
    baseline: dict[int, dict[str, Any]],
    candidate: dict[int, dict[str, Any]],
    baseline_path: Path,
    candidate_path: Path,
    baseline_label: str,
    candidate_label: str,
    max_examples: int,
    completion_chars: int,
) -> str:
    total = len(comparison["indexes"])
    lines = [
        "# Sample Comparison",
        "",
        f"Baseline: `{baseline_path}`",
        f"Candidate: `{candidate_path}`",
        "",
        "## Summary",
        "",
        f"- compared examples: {total}",
        f"- {baseline_label} exact: {comparison['baseline_exact']}/{total}",
        f"- {candidate_label} exact: {comparison['candidate_exact']}/{total}",
        f"- wins: {len(comparison['wins'])} {comparison['wins']}",
        f"- losses: {len(comparison['losses'])} {comparison['losses']}",
        f"- same correct: {len(comparison['same_correct'])}",
        f"- same wrong: {len(comparison['same_wrong'])}",
        (
            f"- final-line format wins: {len(comparison['final_line_wins'])} "
            f"{comparison['final_line_wins']}"
        ),
        (
            f"- final-line format losses: {len(comparison['final_line_losses'])} "
            f"{comparison['final_line_losses']}"
        ),
        "",
    ]
    if comparison["missing_from_baseline"] or comparison["missing_from_candidate"]:
        lines.extend(
            [
                "## Index Mismatch",
                "",
                f"- missing from baseline: {comparison['missing_from_baseline']}",
                f"- missing from candidate: {comparison['missing_from_candidate']}",
                "",
            ]
        )
    lines.extend(
        markdown_section(
            title="Wins",
            indexes=comparison["wins"],
            baseline=baseline,
            candidate=candidate,
            baseline_label=baseline_label,
            candidate_label=candidate_label,
            max_examples=max_examples,
            completion_chars=completion_chars,
        )
    )
    lines.extend(
        markdown_section(
            title="Losses",
            indexes=comparison["losses"],
            baseline=baseline,
            candidate=candidate,
            baseline_label=baseline_label,
            candidate_label=candidate_label,
            max_examples=max_examples,
            completion_chars=completion_chars,
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument("--candidate-label", default="candidate")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-examples", type=int, default=20)
    parser.add_argument("--completion-chars", type=int, default=360)
    args = parser.parse_args()

    baseline_path = resolve_samples_path(args.baseline)
    candidate_path = resolve_samples_path(args.candidate)
    baseline = load_samples(baseline_path)
    candidate = load_samples(candidate_path)
    comparison = compare_records(baseline, candidate)

    render_table(
        comparison,
        baseline_label=args.baseline_label,
        candidate_label=args.candidate_label,
    )

    if args.output:
        report = render_markdown(
            comparison=comparison,
            baseline=baseline,
            candidate=candidate,
            baseline_path=baseline_path,
            candidate_path=candidate_path,
            baseline_label=args.baseline_label,
            candidate_label=args.candidate_label,
            max_examples=args.max_examples,
            completion_chars=args.completion_chars,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
