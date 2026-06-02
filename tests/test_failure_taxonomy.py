from rlvr_lab.failure_taxonomy import summarize_taxonomy, taxonomy_bucket


def sample(
    *,
    exact_correct: bool,
    has_final_format: bool,
    final_line_is_answer: bool,
    has_trailing_text_after_final: bool = False,
    extracted_answer: str | None = "42",
) -> dict[str, object]:
    return {
        "index": 0,
        "prompt": "Problem:\nExample?\n\nSolution:",
        "completion": "work\n#### 42",
        "ground_truth": "42",
        "normalized_ground_truth": "42",
        "extracted_answer": extracted_answer,
        "normalized_answer": extracted_answer,
        "final_line_answer": extracted_answer if final_line_is_answer else None,
        "normalized_final_line_answer": extracted_answer if final_line_is_answer else None,
        "completion_chars": 12,
        "exact_correct": exact_correct,
        "has_final_format": has_final_format,
        "final_line_is_answer": final_line_is_answer,
        "has_trailing_text_after_final": has_trailing_text_after_final,
    }


def test_taxonomy_bucket_separates_clean_math_errors_from_contract_errors() -> None:
    assert (
        taxonomy_bucket(
            sample(
                exact_correct=False,
                has_final_format=True,
                final_line_is_answer=True,
            )
        )
        == "wrong_math_clean_contract"
    )
    assert (
        taxonomy_bucket(
            sample(
                exact_correct=False,
                has_final_format=False,
                final_line_is_answer=False,
            )
        )
        == "wrong_missing_marker"
    )
    assert (
        taxonomy_bucket(
            sample(
                exact_correct=True,
                has_final_format=True,
                final_line_is_answer=False,
                has_trailing_text_after_final=True,
            )
        )
        == "correct_with_trailing_text"
    )


def test_summarize_taxonomy_reports_wrong_clean_contract_rate() -> None:
    records = [
        sample(exact_correct=True, has_final_format=True, final_line_is_answer=True),
        sample(exact_correct=False, has_final_format=True, final_line_is_answer=True),
        sample(exact_correct=False, has_final_format=True, final_line_is_answer=False),
    ]

    summary = summarize_taxonomy(records)

    assert summary["num_examples"] == 3
    assert summary["exact_correct"] == 1
    assert summary["exact_wrong"] == 2
    assert summary["wrong_math_clean_contract_count"] == 1
    assert summary["wrong_math_clean_contract_rate"] == 0.5
    assert summary["wrong_boundary_or_extraction_count"] == 1
    assert summary["bucket_counts"]["correct_clean_contract"] == 1
    assert summary["bucket_counts"]["wrong_marker_not_final_line"] == 1
