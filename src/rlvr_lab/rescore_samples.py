from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rlvr_lab.eval_metrics import score_completion, summarize_records
from rlvr_lab.eval_model import render_summary


def resolve_samples_path(path: Path) -> Path:
    if path.is_dir():
        path = path / "samples.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"samples file does not exist: {path}")
    return path


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_samples(path: Path) -> list[dict[str, Any]]:
    samples_path = resolve_samples_path(path)
    records: list[dict[str, Any]] = []
    with samples_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def rescore_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return score_completion(
        prompt=str(record.get("prompt", "")),
        completion=str(record.get("completion", "")),
        ground_truth=str(record.get("ground_truth", "")),
        index=int(record.get("index", 0)),
    )


def rescore_records(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [rescore_record(record) for record in records]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(data), indent=2, sort_keys=True), encoding="utf-8")


def rescore_samples_dir(samples: Path, output_dir: Path) -> dict[str, Any]:
    samples_path = resolve_samples_path(samples)
    input_dir = samples_path.parent
    rescored = rescore_records(load_samples(samples_path))
    summary = summarize_records(rescored)

    source_summary = load_json(input_dir / "summary.json")
    for key in ["model_name_or_path", "adapter_path", "config_path"]:
        if key in source_summary:
            summary[key] = source_summary[key]
    summary["output_dir"] = str(output_dir)
    summary["rescored_from"] = str(input_dir)

    write_jsonl(output_dir / "samples.jsonl", rescored)
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("samples", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    summary = rescore_samples_dir(args.samples, args.output_dir)
    render_summary(summary)


if __name__ == "__main__":
    main()
