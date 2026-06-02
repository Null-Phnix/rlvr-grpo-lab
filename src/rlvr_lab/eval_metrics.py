from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from rlvr_lab.rewards import (
    FINAL_RE,
    answers_match,
    extract_answer,
    extract_final_line_answer,
    has_text_after_final_marker,
    normalize_answer,
)


def score_completion(
    *,
    prompt: str,
    completion: str,
    ground_truth: str,
    index: int,
) -> dict[str, Any]:
    extracted = extract_answer(completion)
    final_line_answer = extract_final_line_answer(completion)
    normalized_answer = normalize_answer(extracted)
    normalized_final_line_answer = normalize_answer(final_line_answer)
    normalized_ground_truth = normalize_answer(ground_truth)
    exact_correct = answers_match(extracted, ground_truth)

    return {
        "index": index,
        "prompt": prompt,
        "completion": completion,
        "ground_truth": ground_truth,
        "extracted_answer": extracted,
        "final_line_answer": final_line_answer,
        "normalized_answer": normalized_answer,
        "normalized_final_line_answer": normalized_final_line_answer,
        "normalized_ground_truth": normalized_ground_truth,
        "exact_correct": exact_correct,
        "has_final_format": bool(FINAL_RE.search(completion)),
        "final_line_is_answer": final_line_answer is not None,
        "has_trailing_text_after_final": has_text_after_final_marker(completion),
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
            "final_line_format_rate": 0.0,
            "trailing_text_rate": 0.0,
            "missing_answer_rate": 0.0,
            "avg_completion_chars": 0.0,
        }

    exact = sum(1 for record in records if record["exact_correct"])
    final_format = sum(1 for record in records if record["has_final_format"])
    final_line = sum(1 for record in records if record["final_line_is_answer"])
    trailing = sum(1 for record in records if record["has_trailing_text_after_final"])
    missing = sum(1 for record in records if record["extracted_answer"] is None)
    completion_chars = sum(int(record["completion_chars"]) for record in records)

    return {
        "num_examples": total,
        "exact_accuracy": exact / total,
        "final_format_rate": final_format / total,
        "final_line_format_rate": final_line / total,
        "trailing_text_rate": trailing / total,
        "missing_answer_rate": missing / total,
        "avg_completion_chars": completion_chars / total,
        "exact_correct": exact,
        "final_format_count": final_format,
        "final_line_format_count": final_line,
        "trailing_text_count": trailing,
        "missing_answer_count": missing,
    }
