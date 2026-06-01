from rlvr_lab.analyze_samples import (
    analyze_records,
    has_instruction_leak,
    score_stopaware_record,
    text_after_first_marker,
)


def sample(
    *,
    completion: str,
    ground_truth: str = "42",
    exact_correct: bool = False,
    final_line_is_answer: bool = False,
) -> dict[str, object]:
    return {
        "index": 0,
        "prompt": "Problem?",
        "completion": completion,
        "ground_truth": ground_truth,
        "exact_correct": exact_correct,
        "final_line_is_answer": final_line_is_answer,
        "has_final_format": "####" in completion,
        "has_trailing_text_after_final": "\n" in text_after_first_marker(completion),
        "extracted_answer": "42",
        "completion_chars": len(completion),
    }


def test_text_after_first_marker() -> None:
    assert text_after_first_marker("work\n#### 42\nextra") == "\nextra"
    assert text_after_first_marker("work only") == ""


def test_has_instruction_leak_only_checks_after_marker() -> None:
    assert has_instruction_leak("Solve the math problem\n#### 42") is False
    assert has_instruction_leak("work\n#### 42\nSolve the math problem again") is True


def test_score_stopaware_record_truncates_after_marker() -> None:
    record = sample(completion="work\n#### 42\nHuman: retry")
    scored = score_stopaware_record(
        record,
        postprocess_config={
            "truncate_after_final_marker": True,
            "stop_sequences": ["\nHuman:"],
        },
    )

    assert scored["completion"] == "work\n#### 42"
    assert scored["exact_correct"] is True
    assert scored["final_line_is_answer"] is True


def test_analyze_records_reports_stopaware_delta() -> None:
    records = [
        sample(
            completion="work\n#### 42\nHuman: retry",
            exact_correct=True,
            final_line_is_answer=False,
        ),
        sample(
            completion="work\n#### 41\nDo not write anything after it.",
            ground_truth="42",
            exact_correct=False,
            final_line_is_answer=False,
        ),
    ]

    summary = analyze_records(records)

    assert summary["num_examples"] == 2
    assert summary["original"]["exact_correct"] == 1
    assert summary["stopaware"]["exact_correct"] == 1
    assert summary["stopaware"]["final_line_format_count"] == 2
    assert summary["marked_answer_correct_count"] == 1
    assert summary["marked_correct_with_trailing_count"] == 1
    assert summary["role_leak_count"] == 1
    assert summary["instruction_leak_after_marker_count"] == 1
    assert summary["stopaware_final_line_wins"] == 2
    assert summary["stopaware_exact_wins"] == 0
    assert summary["stopaware_exact_losses"] == 0
