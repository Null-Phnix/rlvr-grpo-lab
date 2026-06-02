from __future__ import annotations

import argparse
import json
import math
import random
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from rlvr_lab.compare_samples import load_samples, resolve_samples_path

DEFAULT_METRICS = {
    "exact": "exact_correct",
    "final_line": "final_line_is_answer",
    "final_format": "has_final_format",
    "trailing_text": "has_trailing_text_after_final",
}


def metric_value(record: Mapping[str, Any], field: str) -> int:
    return int(bool(record.get(field, False)))


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def bootstrap_delta_rate(
    deltas: list[int],
    *,
    iterations: int,
    seed: int,
) -> tuple[float, float]:
    if not deltas or iterations <= 0:
        return (0.0, 0.0)

    rng = random.Random(seed)
    total = len(deltas)
    sampled: list[float] = []
    for _ in range(iterations):
        sampled.append(sum(rng.choice(deltas) for _ in range(total)) / total)
    sampled.sort()
    return (percentile(sampled, 0.025), percentile(sampled, 0.975))


def summarize_metric(
    *,
    indexes: list[int],
    baseline: Mapping[int, Mapping[str, Any]],
    candidate: Mapping[int, Mapping[str, Any]],
    field: str,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    baseline_values = [metric_value(baseline[index], field) for index in indexes]
    candidate_values = [metric_value(candidate[index], field) for index in indexes]
    deltas = [
        candidate_value - baseline_value
        for baseline_value, candidate_value in zip(baseline_values, candidate_values, strict=True)
    ]
    total = len(indexes)
    baseline_count = sum(baseline_values)
    candidate_count = sum(candidate_values)
    delta_count = sum(deltas)
    ci_low, ci_high = bootstrap_delta_rate(deltas, iterations=iterations, seed=seed)

    def rate(count: int) -> float:
        return count / total if total else 0.0

    return {
        "baseline_count": baseline_count,
        "candidate_count": candidate_count,
        "delta_count": delta_count,
        "baseline_rate": rate(baseline_count),
        "candidate_rate": rate(candidate_count),
        "delta_rate": rate(delta_count),
        "wins": sum(1 for delta in deltas if delta > 0),
        "losses": sum(1 for delta in deltas if delta < 0),
        "bootstrap_ci95_delta_rate": [ci_low, ci_high],
        "bootstrap_ci95_delta_count": [ci_low * total, ci_high * total],
    }


def compare_with_bootstrap(
    baseline: Mapping[int, Mapping[str, Any]],
    candidate: Mapping[int, Mapping[str, Any]],
    *,
    iterations: int,
    seed: int,
    metrics: Mapping[str, str] = DEFAULT_METRICS,
) -> dict[str, Any]:
    indexes = sorted(set(baseline) & set(candidate))
    if not indexes:
        raise ValueError("baseline and candidate have no overlapping sample indexes")

    metric_summaries: dict[str, Any] = {}
    for offset, (metric_name, field) in enumerate(metrics.items()):
        metric_summaries[metric_name] = summarize_metric(
            indexes=indexes,
            baseline=baseline,
            candidate=candidate,
            field=field,
            iterations=iterations,
            seed=seed + offset,
        )

    return {
        "compared_examples": len(indexes),
        "missing_from_baseline": sorted(set(candidate) - set(baseline)),
        "missing_from_candidate": sorted(set(baseline) - set(candidate)),
        "iterations": iterations,
        "seed": seed,
        "metrics": metric_summaries,
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def render_summary(summary: Mapping[str, Any]) -> None:
    table = Table(title="Paired Bootstrap Comparison")
    table.add_column("Metric")
    table.add_column("Baseline", justify="right")
    table.add_column("Candidate", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("95% CI Delta", justify="right")

    total = int(summary["compared_examples"])
    for metric_name, metric in summary["metrics"].items():
        ci_low, ci_high = metric["bootstrap_ci95_delta_rate"]
        table.add_row(
            metric_name,
            f"{metric['baseline_count']}/{total}",
            f"{metric['candidate_count']}/{total}",
            f"{metric['delta_rate']:.4f}",
            f"[{ci_low:.4f}, {ci_high:.4f}]",
        )

    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    baseline_path = resolve_samples_path(args.baseline)
    candidate_path = resolve_samples_path(args.candidate)
    summary = compare_with_bootstrap(
        load_samples(baseline_path),
        load_samples(candidate_path),
        iterations=args.iterations,
        seed=args.seed,
    )
    summary["baseline_path"] = str(baseline_path)
    summary["candidate_path"] = str(candidate_path)
    render_summary(summary)
    if args.output:
        write_summary(args.output, summary)


if __name__ == "__main__":
    main()
