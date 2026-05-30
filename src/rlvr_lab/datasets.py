from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SYSTEM_PROMPT = (
    "You are solving math problems. Reason briefly. "
    "End with the numeric final answer in this exact format, for example: #### 42"
)

ANSWER_FIRST_PROMPT = (
    "Solve the problem. Keep the reasoning short. "
    "The final line must be exactly four hash marks, a space, and the numeric answer."
)

STRICT_FINAL_LINE_PROMPT = (
    "Solve the math problem with concise reasoning. "
    "Write the final answer as the last non-empty line. "
    "That last line must look like this example: #### 42. "
    "Do not write anything after it."
)

FINAL_ONLY_PROMPT = (
    "Solve the math problem internally. "
    "Output exactly one line and no reasoning. "
    "The line must look like this example: #### 42"
)


def gsm8k_gold_answer(answer: str) -> str:
    """Extract the GSM8K final answer after the #### marker."""
    if "####" in answer:
        return answer.rsplit("####", 1)[-1].strip()
    return answer.strip()


def make_prompt(question: str, prompt_style: str = "think_answer") -> str:
    if prompt_style == "plain":
        return f"{question}\n\nFinal answer:"
    if prompt_style == "answer_first":
        return f"{ANSWER_FIRST_PROMPT}\n\nProblem:\n{question}\n\nAnswer:"
    if prompt_style == "final_only":
        return f"{FINAL_ONLY_PROMPT}\n\nProblem:\n{question}\n\nAnswer:"
    if prompt_style == "strict_final_line":
        return f"{STRICT_FINAL_LINE_PROMPT}\n\nProblem:\n{question}\n\nSolution:"
    if prompt_style == "think_answer":
        return f"{SYSTEM_PROMPT}\n\nProblem:\n{question}\n\nSolution:"
    raise ValueError(f"unknown prompt_style: {prompt_style}")


def prepare_gsm8k_row(row: Mapping[str, Any], prompt_style: str = "think_answer") -> dict[str, str]:
    return {
        "prompt": make_prompt(str(row["question"]), prompt_style=prompt_style),
        "ground_truth": gsm8k_gold_answer(str(row["answer"])),
    }


def load_math_dataset(config: Mapping[str, Any]):
    """Load and normalize the configured math dataset for TRL GRPO."""
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    dataset_name = config.get("name", "openai/gsm8k")
    dataset_config = config.get("config", "main")
    split = config.get("split", "train")
    prompt_style = config.get("prompt_style", "think_answer")
    limit = config.get("limit")

    dataset = load_dataset(dataset_name, dataset_config, split=split)
    if limit:
        dataset = dataset.select(range(min(int(limit), len(dataset))))

    return dataset.map(
        lambda row: prepare_gsm8k_row(row, prompt_style=prompt_style),
        remove_columns=dataset.column_names,
    )
