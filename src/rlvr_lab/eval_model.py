from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.progress import track
from rich.table import Table

from rlvr_lab.datasets import load_math_dataset
from rlvr_lab.eval_metrics import score_completion, summarize_records


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


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


def load_model_and_tokenizer(config: dict[str, Any], adapter_path: str | None):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = str(config["model_name_or_path"])
    model_config = config.get("model", {})
    dtype = resolve_dtype(str(model_config.get("torch_dtype", "auto")))
    device_map = model_config.get("device_map", "auto" if torch.cuda.is_available() else None)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    kwargs: dict[str, Any] = {"dtype": dtype}
    if device_map:
        kwargs["device_map"] = device_map

    model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    if adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_path)

    if not device_map and torch.cuda.is_available():
        model = model.to("cuda")

    model.eval()
    return model, tokenizer


def generate_batch(
    *,
    model,
    tokenizer,
    prompts: list[str],
    generation_config: dict[str, Any],
) -> list[str]:
    import torch

    max_prompt_length = int(generation_config.get("max_prompt_length", 512))
    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_prompt_length,
    )
    inputs = {key: value.to(model.device) for key, value in inputs.items()}

    do_sample = bool(generation_config.get("do_sample", False))
    generate_kwargs: dict[str, Any] = {
        "max_new_tokens": int(generation_config.get("max_new_tokens", 128)),
        "do_sample": do_sample,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if do_sample:
        generate_kwargs["temperature"] = float(generation_config.get("temperature", 0.8))
        generate_kwargs["top_p"] = float(generation_config.get("top_p", 0.95))

    with torch.no_grad():
        output_ids = model.generate(**inputs, **generate_kwargs)

    input_width = inputs["input_ids"].shape[1]
    completions = []
    for output in output_ids:
        completion_ids = output[input_width:]
        completions.append(tokenizer.decode(completion_ids, skip_special_tokens=True).strip())
    return completions


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def render_summary(summary: dict[str, Any]) -> None:
    table = Table(title="Eval Summary")
    table.add_column("Metric")
    table.add_column("Value")
    for key in [
        "num_examples",
        "exact_accuracy",
        "final_format_rate",
        "missing_answer_rate",
        "avg_completion_chars",
    ]:
        table.add_row(key, str(summary[key]))
    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--adapter-path", type=str)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = args.output_dir or Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_math_dataset(config["dataset"])
    model, tokenizer = load_model_and_tokenizer(config, args.adapter_path)

    generation_config = config.get("generation", {})
    batch_size = int(generation_config.get("batch_size", 1))
    records: list[dict[str, Any]] = []
    total_batches = (len(dataset) + batch_size - 1) // batch_size

    for start in track(
        range(0, len(dataset), batch_size),
        total=total_batches,
        description="Evaluating",
    ):
        batch = dataset[start : start + batch_size]
        prompts = list(batch["prompt"])
        ground_truths = list(batch["ground_truth"])
        completions = generate_batch(
            model=model,
            tokenizer=tokenizer,
            prompts=prompts,
            generation_config=generation_config,
        )
        for offset, (prompt, completion, ground_truth) in enumerate(
            zip(prompts, completions, ground_truths, strict=True)
        ):
            records.append(
                score_completion(
                    prompt=prompt,
                    completion=completion,
                    ground_truth=ground_truth,
                    index=start + offset,
                )
            )

    summary = summarize_records(records)
    summary.update(
        {
            "model_name_or_path": config["model_name_or_path"],
            "adapter_path": args.adapter_path,
            "config_path": str(args.config),
            "output_dir": str(output_dir),
        }
    )

    write_jsonl(output_dir / "samples.jsonl", records)
    write_summary(output_dir / "summary.json", summary)
    render_summary(summary)


if __name__ == "__main__":
    main()
