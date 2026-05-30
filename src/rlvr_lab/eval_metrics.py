from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from rlvr_lab.rewards import FINAL_RE, extract_answer, normalize_answer


def score_completion(
    *,
    prompt: str,
    completion: str,
    ground_truth: str,
    index: int,
) -> dict[str, Any]:
    extracted = extract_answer(completion)
    normalized_answer = normalize_answer(extracted)
    normalized_ground_truth = normalize_answer(ground_truth)
    exact_correct = (
        normalized_answer is not None
        and normalized_ground_truth is not None
        and normalized_answer == normalized_ground_truth
    )

    return {
        "index": index,
        "prompt": prompt,
        "completion": completion,
        "ground_truth": ground_truth,
        "extracted_answer": extracted,
        "normalized_answer": normalized_answer,
        "normalized_ground_truth": normalized_ground_truth,
        "exact_correct": exact_correct,
        "has_final_format": bool(FINAL_RE.search(completion)),
        "prompt_chars": len(prompt),
        "completion_chars": len(completion),
    }


def summarize_records(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    if total == 0:
        return {
            "num_examples": 0,
            "exact_accuracy": 0.0,
            "final_format_rate": 0.0,
            "missing_answer_rate": 0.0,
            "avg_completion_chars": 0.0,
        }

    exact = sum(1 for record in records if record["exact_correct"])
    final_format = sum(1 for record in records if record["has_final_format"])
    missing = sum(1 for record in records if record["extracted_answer"] is None)
    completion_chars = sum(int(record["completion_chars"]) for record in records)

    return {
        "num_examples": total,
        "exact_accuracy": exact / total,
        "final_format_rate": final_format / total,
        "missing_answer_rate": missing / total,
        "avg_completion_chars": completion_chars / total,
        "exact_correct": exact,
        "final_format_count": final_format,
        "missing_answer_count": missing,
    }
