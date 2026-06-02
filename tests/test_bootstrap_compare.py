from rlvr_lab.bootstrap_compare import compare_with_bootstrap, percentile, summarize_metric


def sample(
    *,
    exact_correct: bool,
    final_line_is_answer: bool = True,
    has_final_format: bool = True,
    has_trailing_text_after_final: bool = False,
) -> dict[str, object]:
    return {
        "exact_correct": exact_correct,
        "final_line_is_answer": final_line_is_answer,
        "has_final_format": has_final_format,
        "has_trailing_text_after_final": has_trailing_text_after_final,
    }


def test_percentile_interpolates_sorted_values() -> None:
    assert percentile([0.0, 10.0], 0.5) == 5.0
    assert percentile([1.0, 2.0, 3.0], 0.5) == 2.0


def test_summarize_metric_reports_paired_wins_losses_and_ci() -> None:
    baseline = {
        0: sample(exact_correct=False),
        1: sample(exact_correct=True),
        2: sample(exact_correct=True),
    }
    candidate = {
        0: sample(exact_correct=True),
        1: sample(exact_correct=False),
        2: sample(exact_correct=True),
    }

    summary = summarize_metric(
        indexes=[0, 1, 2],
        baseline=baseline,
        candidate=candidate,
        field="exact_correct",
        iterations=100,
        seed=7,
    )

    assert summary["baseline_count"] == 2
    assert summary["candidate_count"] == 2
    assert summary["delta_count"] == 0
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert len(summary["bootstrap_ci95_delta_rate"]) == 2


def test_compare_with_bootstrap_compares_overlap_only() -> None:
    baseline = {
        0: sample(exact_correct=False),
        1: sample(exact_correct=True),
    }
    candidate = {
        0: sample(exact_correct=True),
        2: sample(exact_correct=True),
    }

    summary = compare_with_bootstrap(
        baseline,
        candidate,
        iterations=100,
        seed=7,
        metrics={"exact": "exact_correct"},
    )

    assert summary["compared_examples"] == 1
    assert summary["missing_from_baseline"] == [2]
    assert summary["missing_from_candidate"] == [1]
    assert summary["metrics"]["exact"]["delta_count"] == 1
