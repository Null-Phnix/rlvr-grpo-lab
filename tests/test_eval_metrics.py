from rlvr_lab.eval_metrics import score_completion, summarize_records


def test_score_completion_marks_exact_correct() -> None:
    record = score_completion(
        prompt="What is 40 + 2?",
        completion="40 + 2 = 42\n#### 42",
        ground_truth="42",
        index=0,
    )

    assert record["exact_correct"] is True
    assert record["has_final_format"] is True
    assert record["extracted_answer"] == "42"
    assert record["normalized_answer"] == "42"


def test_score_completion_handles_missing_answer() -> None:
    record = score_completion(
        prompt="What is 40 + 2?",
        completion="I do not know.",
        ground_truth="42",
        index=0,
    )

    assert record["exact_correct"] is False
    assert record["has_final_format"] is False
    assert record["extracted_answer"] is None


def test_summarize_records() -> None:
    records = [
        {
            "exact_correct": True,
            "has_final_format": True,
            "extracted_answer": "1",
            "completion_chars": 10,
        },
        {
            "exact_correct": False,
            "has_final_format": False,
            "extracted_answer": None,
            "completion_chars": 30,
        },
    ]

    summary = summarize_records(records)

    assert summary["num_examples"] == 2
    assert summary["exact_accuracy"] == 0.5
    assert summary["final_format_rate"] == 0.5
    assert summary["missing_answer_rate"] == 0.5
    assert summary["avg_completion_chars"] == 20
