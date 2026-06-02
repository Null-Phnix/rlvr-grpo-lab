from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

FINAL_RE = re.compile(r"####\s*([-+]?(?:\d[\d,]*)(?:\.\d+)?)")
FINAL_LINE_RE = re.compile(r"^####\s*([-+]?(?:\d[\d,]*)(?:\.\d+)?)\s*$")
BOXED_RE = re.compile(r"\\boxed\{([^{}]+)\}")
NUMBER_RE = re.compile(r"[-+]?(?:\d[\d,]*)(?:\.\d+)?")
ROLE_LABEL_RE = re.compile(r"\b(?:Human|Assistant|User|System)\s*:")
NUMERIC_MATCH_TOLERANCE = Decimal("1e-9")


def completion_text(completion: Any) -> str:
    """Support TRL standard strings and conversational message dictionaries."""
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list) and completion:
        first = completion[0]
        if isinstance(first, dict):
            return str(first.get("content", ""))
    return str(completion)


def normalize_answer(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "")
    cleaned = cleaned.strip("$% ")
    if not cleaned:
        return None
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return cleaned.lower()
    nearest_integer = number.to_integral_value()
    if abs(number - nearest_integer) <= NUMERIC_MATCH_TOLERANCE:
        number = nearest_integer
    normalized = format(number.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized


def decimal_answer(value: str | None) -> Decimal | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "")
    cleaned = cleaned.strip("$% ")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def answers_match(predicted: str | None, expected: str | None) -> bool:
    predicted_decimal = decimal_answer(predicted)
    expected_decimal = decimal_answer(expected)
    if predicted_decimal is not None and expected_decimal is not None:
        return abs(predicted_decimal - expected_decimal) <= NUMERIC_MATCH_TOLERANCE

    normalized_predicted = normalize_answer(predicted)
    normalized_expected = normalize_answer(expected)
    return (
        normalized_predicted is not None
        and normalized_expected is not None
        and normalized_predicted == normalized_expected
    )


def extract_answer(text: str) -> str | None:
    final_match = FINAL_RE.search(text)
    if final_match:
        return final_match.group(1)

    boxed_match = BOXED_RE.search(text)
    if boxed_match:
        return boxed_match.group(1)

    numbers = NUMBER_RE.findall(text)
    if numbers:
        return numbers[-1]
    return None


def extract_marked_answer(text: str) -> str | None:
    match = FINAL_RE.search(text)
    return match.group(1) if match else None


def final_answer_line(text: str) -> str | None:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return None
    return lines[-1]


def extract_final_line_answer(text: str) -> str | None:
    line = final_answer_line(text)
    if line is None:
        return None
    match = FINAL_LINE_RE.match(line)
    return match.group(1) if match else None


def has_text_after_final_marker(text: str) -> bool:
    match = FINAL_RE.search(text)
    if not match:
        return False
    return bool(text[match.end() :].strip())


def has_role_label(text: str) -> bool:
    return bool(ROLE_LABEL_RE.search(text))


def math_correctness_reward(
    completions: list[Any],
    ground_truth: list[str],
    **kwargs: Any,
) -> list[float]:
    rewards = []
    extracted = []
    for completion, gold in zip(completions, ground_truth, strict=False):
        predicted = extract_answer(completion_text(completion))
        extracted.append(normalize_answer(predicted) or "[none]")
        rewards.append(1.0 if answers_match(predicted, gold) else 0.0)

    log_extra = kwargs.get("log_extra")
    if log_extra:
        log_extra("gold_answer", list(ground_truth))
        log_extra("extracted_answer", extracted)

    log_metric = kwargs.get("log_metric")
    if log_metric and rewards:
        log_metric("exact_answer_accuracy", sum(rewards) / len(rewards))

    return rewards


def final_line_correctness_reward(
    completions: list[Any],
    ground_truth: list[str],
    **kwargs: Any,
) -> list[float]:
    rewards = []
    extracted = []
    for completion, gold in zip(completions, ground_truth, strict=False):
        predicted = extract_final_line_answer(completion_text(completion))
        extracted.append(normalize_answer(predicted) or "[none]")
        rewards.append(1.0 if answers_match(predicted, gold) else 0.0)

    log_extra = kwargs.get("log_extra")
    if log_extra:
        log_extra("final_line_extracted_answer", extracted)

    log_metric = kwargs.get("log_metric")
    if log_metric and rewards:
        log_metric("final_line_exact_accuracy", sum(rewards) / len(rewards))

    return rewards


def answer_marker_correctness_reward(
    completions: list[Any],
    ground_truth: list[str],
    **kwargs: Any,
) -> list[float]:
    rewards = []
    extracted = []
    for completion, gold in zip(completions, ground_truth, strict=False):
        predicted = extract_marked_answer(completion_text(completion))
        extracted.append(normalize_answer(predicted) or "[none]")
        rewards.append(1.0 if answers_match(predicted, gold) else 0.0)

    log_extra = kwargs.get("log_extra")
    if log_extra:
        log_extra("marked_answer", extracted)

    log_metric = kwargs.get("log_metric")
    if log_metric and rewards:
        log_metric("marked_answer_exact_accuracy", sum(rewards) / len(rewards))

    return rewards


def answer_contract_progress_reward(
    completions: list[Any],
    ground_truth: list[str],
    **kwargs: Any,
) -> list[float]:
    rewards = []
    marker_count = 0
    marker_correct_count = 0
    clean_stop_count = 0
    role_leak_count = 0

    for completion, gold in zip(completions, ground_truth, strict=False):
        text = completion_text(completion)
        marked_answer = extract_marked_answer(text)
        has_marker = marked_answer is not None
        marker_correct = has_marker and answers_match(marked_answer, gold)
        clean_stop = has_marker and not has_text_after_final_marker(text)
        role_leak = has_role_label(text)

        marker_count += int(has_marker)
        marker_correct_count += int(marker_correct)
        clean_stop_count += int(clean_stop)
        role_leak_count += int(role_leak)

        score = 0.0
        if has_marker:
            score += 0.15
        if marker_correct:
            score += 0.50
            if not role_leak:
                score += 0.10
            if clean_stop:
                score += 0.25
        rewards.append(score)

    log_metric = kwargs.get("log_metric")
    if log_metric and rewards:
        total = len(rewards)
        log_metric("contract_marker_rate", marker_count / total)
        log_metric("contract_marker_exact_rate", marker_correct_count / total)
        log_metric("contract_clean_stop_rate", clean_stop_count / total)
        log_metric("contract_role_leak_rate", role_leak_count / total)
        log_metric("answer_contract_progress", sum(rewards) / total)

    return rewards


def final_format_reward(completions: list[Any], **kwargs: Any) -> list[float]:
    return [
        1.0 if FINAL_RE.search(completion_text(completion)) else 0.0
        for completion in completions
    ]


def final_line_format_reward(completions: list[Any], **kwargs: Any) -> list[float]:
    return [
        1.0 if extract_final_line_answer(completion_text(completion)) is not None else 0.0
        for completion in completions
    ]


def trailing_text_penalty(completions: list[Any], **kwargs: Any) -> list[float]:
    return [
        -1.0 if has_text_after_final_marker(completion_text(completion)) else 0.0
        for completion in completions
    ]


def conversation_leak_penalty(completions: list[Any], **kwargs: Any) -> list[float]:
    rewards = [
        -1.0 if has_role_label(completion_text(completion)) else 0.0
        for completion in completions
    ]

    log_metric = kwargs.get("log_metric")
    if log_metric and rewards:
        log_metric("conversation_leak_rate", abs(sum(rewards)) / len(rewards))

    return rewards
