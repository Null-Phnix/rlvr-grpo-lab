from __future__ import annotations

import argparse
import inspect
from pathlib import Path
from typing import Any

import yaml

from rlvr_lab.datasets import load_math_dataset
from rlvr_lab.rewards import (
    final_format_reward,
    final_line_correctness_reward,
    final_line_format_reward,
    math_correctness_reward,
    trailing_text_penalty,
)


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_lora_config(config: dict[str, Any]):
    if config.get("adapter_path"):
        return None

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
        from trl import GRPOConfig
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    training = config.get("training", {})
    reward_weights = config.get("rewards", {})
    requested_args = {
        "output_dir": str(config["output_dir"]),
        "seed": int(config.get("seed", 42)),
        "max_steps": int(training.get("max_steps", 25)),
        "learning_rate": float(training.get("learning_rate", 5e-6)),
        "per_device_train_batch_size": int(training.get("per_device_train_batch_size", 1)),
        "gradient_accumulation_steps": int(training.get("gradient_accumulation_steps", 4)),
        "num_generations": int(training.get("num_generations", 2)),
        "max_prompt_length": int(training.get("max_prompt_length", 512)),
        "max_completion_length": int(training.get("max_completion_length", 128)),
        "temperature": float(training.get("temperature", 0.8)),
        "top_p": float(training.get("top_p", 0.95)),
        "logging_steps": int(training.get("logging_steps", 1)),
        "save_steps": int(training.get("save_steps", 25)),
        "bf16": bool(training.get("bf16", False)),
        "fp16": bool(training.get("fp16", False)),
        "gradient_checkpointing": bool(training.get("gradient_checkpointing", True)),
        "use_vllm": bool(training.get("use_vllm", False)),
        "beta": float(training.get("beta", 0.0)),
        "loss_type": str(training.get("loss_type", "dr_grpo")),
        "reward_weights": [
            float(reward_weights.get("correctness_weight", 1.0)),
            float(reward_weights.get("final_line_correctness_weight", 0.0)),
            float(reward_weights.get("format_weight", 0.2)),
            float(reward_weights.get("final_line_weight", 0.0)),
            float(reward_weights.get("trailing_penalty_weight", 0.0)),
        ],
        "report_to": "none",
        "remove_unused_columns": False,
    }

    supported_args = set(inspect.signature(GRPOConfig.__init__).parameters)
    filtered_args = {
        name: value for name, value in requested_args.items() if name in supported_args
    }
    return GRPOConfig(**filtered_args)


def resolve_resume_from_checkpoint(config: dict[str, Any]) -> bool | str | None:
    resume_from_checkpoint = config.get("training", {}).get("resume_from_checkpoint")
    if resume_from_checkpoint in {None, False, ""}:
        return None
    if resume_from_checkpoint is True:
        return True

    checkpoint_path = Path(str(resume_from_checkpoint))
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"resume checkpoint does not exist: {checkpoint_path}")
    return str(checkpoint_path)


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


def load_model(config: dict[str, Any]):
    adapter_path = config.get("adapter_path")
    if not adapter_path:
        return str(config["model_name_or_path"])

    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    model_config = config.get("model", {})
    dtype = resolve_dtype(str(model_config.get("torch_dtype", "auto")))
    model = AutoModelForCausalLM.from_pretrained(
        str(config["model_name_or_path"]),
        dtype=dtype,
    )
    if torch.cuda.is_available():
        model = model.to("cuda")
    model = PeftModel.from_pretrained(model, str(adapter_path), is_trainable=True)
    model.config.use_cache = False
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    dataset = load_math_dataset(config["dataset"])

    try:
        from trl import GRPOTrainer
    except ImportError as exc:  # pragma: no cover - train extra only
        raise RuntimeError("Install training dependencies with `uv sync --extra train`.") from exc

    training_args = build_training_args(config)

    trainer = GRPOTrainer(
        model=load_model(config),
        args=training_args,
        train_dataset=dataset,
        reward_funcs=[
            math_correctness_reward,
            final_line_correctness_reward,
            final_format_reward,
            final_line_format_reward,
            trailing_text_penalty,
        ],
        peft_config=build_lora_config(config),
    )
    trainer.train(resume_from_checkpoint=resolve_resume_from_checkpoint(config))


if __name__ == "__main__":
    main()
