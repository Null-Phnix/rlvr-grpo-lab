from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rlvr_lab.rewards import FINAL_RE


def cut_at_first_stop(text: str, stop_sequences: Sequence[str]) -> str:
    stops = [stop for stop in stop_sequences if stop]
    if not stops:
        return text

    indexes = [text.find(stop) for stop in stops]
    indexes = [index for index in indexes if index >= 0]
    if not indexes:
        return text
    return text[: min(indexes)]


def truncate_after_final_marker(text: str) -> str:
    match = FINAL_RE.search(text)
    if not match:
        return text
    return text[: match.end()]


def postprocess_completion(text: str, config: Mapping[str, Any] | None = None) -> str:
    if not config:
        return text.strip()

    processed = text
    processed = cut_at_first_stop(processed, list(config.get("stop_sequences", [])))
    if bool(config.get("truncate_after_final_marker", False)):
        processed = truncate_after_final_marker(processed)
    return processed.strip()


def postprocess_completions(
    completions: Sequence[str],
    config: Mapping[str, Any] | None = None,
) -> list[str]:
    return [postprocess_completion(completion, config) for completion in completions]
