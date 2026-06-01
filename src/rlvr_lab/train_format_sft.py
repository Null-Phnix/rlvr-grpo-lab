from __future__ import annotations

import argparse
import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from rlvr_lab.datasets import gsm8k_gold_answer, make_prompt


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def format_sft_completion(answer: str, eos_token: str | None) -> str:
    eos = eos_token or ""
    return f"\n#### {answer.strip()}{eos}"


def format_gsm8k_rationale_completion(answer: str, eos_token: str | None) -> str:
    eos = eos_token or ""
    return f"\n{answer.strip()}{eos}"


def format_sample_completion(completion: str, eos_token: str | None) -> str:
    eos = eos_token or ""
    text = completion.strip()
    if text and not text[0].isspace():
        text = f"\n{text}"
    if eos and not text.endswith(eos):
        text = f"{text}{eos}"
    return text


def build_sft_completion(row: dict[str, Any], completion_style: str, eos_token: str | None) -> str:
    if completion_style == "final_only":
        return format_sft_completion(gsm8k_gold_answer(str(row["answer"])), eos_token)
    if completion_style == "gsm8k_rationale":
        return format_gsm8k_rationale_completion(str(row["answer"]), eos_token)
    if completion_style == "sample_completion":
        return format_sample_completion(str(row["completion"]), eos_token)
    raise ValueError(f"unknown completion_style: {completion_style}")


def resolve_dtype(dtype_name: str):
    import torch

    if dtype_name == "auto":
        return "auto"
    if dtype_name in {"float16", "fp16"}:
        return torch.float16
    if dtype_name in {"bfloat16", "bf16"}:
        return torch.bfloat16
    if dtype_name in {"float32", "fp32"}:
        return torch.float32
    raise ValueError(f"unknown torch dtype: {dtype_name}")


def build_lora_config(config: dict[str, Any]):
    lora = config.get("lora", {})
    if not lora.get("enabled", False):
        return None

    try:
        from peft import LoraConfig
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    return LoraConfig(
        r=int(lora.get("r", 16)),
        lora_alpha=int(lora.get("alpha", 32)),
        lora_dropout=float(lora.get("dropout", 0.05)),
        target_modules=list(lora.get("target_modules", [])),
        task_type="CAUSAL_LM",
    )


def build_training_args(config: dict[str, Any]):
    try:
        from transformers import TrainingArguments
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    training = config.get("training", {})
    requested_args = {
        "output_dir": str(config["output_dir"]),
        "seed": int(config.get("seed", 42)),
        "max_steps": int(training.get("max_steps", 60)),
        "learning_rate": float(training.get("learning_rate", 2e-4)),
        "per_device_train_batch_size": int(training.get("per_device_train_batch_size", 4)),
        "gradient_accumulation_steps": int(training.get("gradient_accumulation_steps", 1)),
        "logging_steps": int(training.get("logging_steps", 5)),
        "save_steps": int(training.get("save_steps", 60)),
        "save_strategy": "steps",
        "bf16": bool(training.get("bf16", False)),
        "fp16": bool(training.get("fp16", False)),
        "gradient_checkpointing": bool(training.get("gradient_checkpointing", True)),
        "report_to": "none",
        "remove_unused_columns": False,
    }

    supported_args = set(inspect.signature(TrainingArguments.__init__).parameters)
    filtered_args = {
        name: value for name, value in requested_args.items() if name in supported_args
    }
    return TrainingArguments(**filtered_args)


def tokenize_prompt_completion(
    *,
    tokenizer,
    prompt: str,
    completion: str,
    max_seq_length: int,
) -> dict[str, list[int]]:
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    full_ids = tokenizer(prompt + completion, add_special_tokens=False)["input_ids"]
    full_ids = full_ids[:max_seq_length]
    label_start = min(len(prompt_ids), len(full_ids))
    labels = [-100] * label_start + full_ids[label_start:]
    return {
        "input_ids": full_ids,
        "attention_mask": [1] * len(full_ids),
        "labels": labels,
    }


def load_sample_completion_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            prompt = str(record.get("prompt", ""))
            completion = str(record.get("completion", ""))
            if not prompt.strip() or not completion.strip():
                continue
            rows.append({"prompt": prompt, "completion": completion})
            if limit is not None and len(rows) >= limit:
                break
    return rows


def load_format_sft_dataset(config: dict[str, Any], tokenizer):
    try:
        from datasets import Dataset, load_dataset
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    dataset_config = config["dataset"]
    dataset = load_dataset(
        dataset_config.get("name", "openai/gsm8k"),
        dataset_config.get("config", "main"),
        split=dataset_config.get("split", "train"),
    )
    limit = dataset_config.get("limit")
    if limit:
        dataset = dataset.select(range(min(int(limit), len(dataset))))

    prompt_style = dataset_config.get("prompt_style", "final_only")
    completion_style = dataset_config.get("completion_style", "final_only")
    max_seq_length = int(config.get("training", {}).get("max_seq_length", 512))
    rows = []
    for row in dataset:
        prompt = make_prompt(str(row["question"]), prompt_style=prompt_style)
        completion = build_sft_completion(dict(row), completion_style, tokenizer.eos_token)
        rows.append(
            tokenize_prompt_completion(
                tokenizer=tokenizer,
                prompt=prompt,
                completion=completion,
                max_seq_length=max_seq_length,
            )
        )

    return Dataset.from_list(rows)


def load_boundary_sft_dataset(config: dict[str, Any], tokenizer):
    try:
        from datasets import Dataset
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    dataset_config = config["dataset"]
    path = Path(str(dataset_config["path"]))
    limit = dataset_config.get("limit")
    max_seq_length = int(config.get("training", {}).get("max_seq_length", 512))
    rows = []
    for row in load_sample_completion_rows(
        path,
        limit=int(limit) if limit else None,
    ):
        completion = build_sft_completion(row, "sample_completion", tokenizer.eos_token)
        rows.append(
            tokenize_prompt_completion(
                tokenizer=tokenizer,
                prompt=row["prompt"],
                completion=completion,
                max_seq_length=max_seq_length,
            )
        )

    return Dataset.from_list(rows)


def load_sft_dataset(config: dict[str, Any], tokenizer):
    dataset_config = config["dataset"]
    if dataset_config.get("source") == "samples_jsonl":
        return load_boundary_sft_dataset(config, tokenizer)
    return load_format_sft_dataset(config, tokenizer)


@dataclass
class CausalSFTCollator:
    tokenizer: Any

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch

        pad_id = int(self.tokenizer.pad_token_id)
        max_length = max(len(feature["input_ids"]) for feature in features)
        batch = {"input_ids": [], "attention_mask": [], "labels": []}
        for feature in features:
            pad_length = max_length - len(feature["input_ids"])
            batch["input_ids"].append(feature["input_ids"] + [pad_id] * pad_length)
            batch["attention_mask"].append(feature["attention_mask"] + [0] * pad_length)
            batch["labels"].append(feature["labels"] + [-100] * pad_length)
        return {key: torch.tensor(value) for key, value in batch.items()}


def load_model_and_tokenizer(config: dict[str, Any]):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = str(config["model_name_or_path"])
    model_config = config.get("model", {})
    dtype = resolve_dtype(str(model_config.get("torch_dtype", "auto")))

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    kwargs: dict[str, Any] = {"dtype": dtype}
    model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    if torch.cuda.is_available():
        model = model.to("cuda")
    return model, tokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = load_config(args.config)

    try:
        from peft import get_peft_model
        from transformers import Trainer, set_seed
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    set_seed(int(config.get("seed", 42)))
    model, tokenizer = load_model_and_tokenizer(config)
    lora_config = build_lora_config(config)
    if lora_config is not None:
        model = get_peft_model(model, lora_config)
    if bool(config.get("training", {}).get("gradient_checkpointing", True)):
        model.config.use_cache = False

    train_dataset = load_sft_dataset(config, tokenizer)
    trainer = Trainer(
        model=model,
        args=build_training_args(config),
        train_dataset=train_dataset,
        data_collator=CausalSFTCollator(tokenizer),
    )
    trainer.train()
    trainer.save_model(str(config["output_dir"]))
    tokenizer.save_pretrained(str(config["output_dir"]))


if __name__ == "__main__":
    main()
