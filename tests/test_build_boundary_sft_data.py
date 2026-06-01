import json

from rlvr_lab.build_boundary_sft_data import (
    build_boundary_records,
    load_samples,
    marked_answer_is_correct,
)


def sample(
    *,
    completion: str,
    ground_truth: str = "42",
    exact_correct: bool = True,
) -> dict[str, object]:
    return {
        "index": 7,
        "prompt": "Problem?\n\nSolution:",
        "completion": completion,
        "ground_truth": ground_truth,
        "exact_correct": exact_correct,
        "final_line_is_answer": False,
        "completion_chars": len(completion),
    }


def test_marked_answer_is_correct_requires_hash_marker() -> None:
    assert marked_answer_is_correct(sample(completion="work\n#### 42\nextra")) is True
    assert marked_answer_is_correct(sample(completion="work answer is 42")) is False
    assert marked_answer_is_correct(sample(completion="work\n#### 41\nextra")) is False


def test_build_boundary_records_filters_and_truncates_to_marker() -> None:
    records = [
        sample(completion="work\n#### 42\nHuman: retry"),
        sample(completion="work answer is 42"),
        sample(completion="work\n#### 42", exact_correct=False),
    ]

    selected, summary = build_boundary_records(records)

    assert selected == [
        {
            "prompt": "Problem?\n\nSolution:",
            "completion": "work\n#### 42",
            "ground_truth": "42",
            "source_index": 7,
            "source_exact_correct": True,
            "source_final_line_is_answer": False,
            "source_completion_chars": len("work\n#### 42\nHuman: retry"),
        }
    ]
    assert summary["input_count"] == 3
    assert summary["selected_count"] == 1
    assert summary["skipped_not_exact"] == 1
    assert summary["skipped_marker_wrong"] == 1


def test_build_boundary_records_can_allow_unmarked_exact() -> None:
    selected, summary = build_boundary_records(
        [sample(completion="work answer is 42")],
        require_marked_correct=False,
    )

    assert selected[0]["completion"] == "work answer is 42"
    assert summary["selected_count"] == 1


def test_load_samples_accepts_eval_directory(tmp_path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    samples_path = eval_dir / "samples.jsonl"
    samples_path.write_text(json.dumps(sample(completion="work\n#### 42")) + "\n")

    records = load_samples(eval_dir)

    assert len(records) == 1
    assert records[0]["completion"] == "work\n#### 42"
