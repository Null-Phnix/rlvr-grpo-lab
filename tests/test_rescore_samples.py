import json

from rlvr_lab.rescore_samples import rescore_samples_dir


def test_rescore_samples_writes_new_output_dir(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.json").write_text(
        json.dumps(
            {
                "model_name_or_path": "model",
                "adapter_path": None,
                "config_path": "configs/eval.yaml",
            }
        )
    )
    (source / "samples.jsonl").write_text(
        json.dumps(
            {
                "index": 0,
                "prompt": "How long?",
                "completion": "30 / 6 = 5.000000000000001\n#### 5.000000000000001",
                "ground_truth": "5",
                "exact_correct": False,
            }
        )
        + "\n"
    )

    output = tmp_path / "rescored"
    summary = rescore_samples_dir(source, output)
    records = [
        json.loads(line)
        for line in (output / "samples.jsonl").read_text().splitlines()
        if line.strip()
    ]

    assert summary["exact_correct"] == 1
    assert summary["model_name_or_path"] == "model"
    assert summary["rescored_from"] == str(source)
    assert records[0]["exact_correct"] is True
