import json
from pathlib import Path

from rlvr_lab.compare_samples import (
    compare_records,
    load_samples,
    render_markdown,
    resolve_samples_path,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def sample(
    index: int,
    *,
    exact_correct: bool,
    final_line_is_answer: bool,
    answer: str,
    ground_truth: str = "42",
) -> dict:
    return {
        "index": index,
        "prompt": f"Problem:\nExample {index}?\n\nSolution:",
        "completion": f"work\n#### {answer}",
        "normalized_ground_truth": ground_truth,
        "normalized_final_line_answer": answer,
        "normalized_answer": answer,
        "extracted_answer": answer,
        "exact_correct": exact_correct,
        "final_line_is_answer": final_line_is_answer,
    }


def test_resolve_samples_path_accepts_eval_directory(tmp_path: Path) -> None:
    samples_path = tmp_path / "eval" / "samples.jsonl"
    write_jsonl(
        samples_path,
        [sample(0, exact_correct=True, final_line_is_answer=True, answer="42")],
    )

    assert resolve_samples_path(tmp_path / "eval") == samples_path


def test_load_samples_indexes_records(tmp_path: Path) -> None:
    samples_path = tmp_path / "samples.jsonl"
    write_jsonl(
        samples_path,
        [
            sample(2, exact_correct=False, final_line_is_answer=True, answer="41"),
            sample(4, exact_correct=True, final_line_is_answer=True, answer="42"),
        ],
    )

    records = load_samples(samples_path)

    assert sorted(records) == [2, 4]
    assert records[4]["exact_correct"] is True


def test_compare_records_tracks_wins_losses_and_format_changes() -> None:
    baseline = {
        0: sample(0, exact_correct=False, final_line_is_answer=False, answer="41"),
        1: sample(1, exact_correct=True, final_line_is_answer=True, answer="42"),
        2: sample(2, exact_correct=True, final_line_is_answer=True, answer="42"),
        3: sample(3, exact_correct=False, final_line_is_answer=False, answer="39"),
    }
    candidate = {
        0: sample(0, exact_correct=True, final_line_is_answer=True, answer="42"),
        1: sample(1, exact_correct=False, final_line_is_answer=False, answer="41"),
        2: sample(2, exact_correct=True, final_line_is_answer=True, answer="42"),
        4: sample(4, exact_correct=True, final_line_is_answer=True, answer="42"),
    }

    comparison = compare_records(baseline, candidate)

    assert comparison["indexes"] == [0, 1, 2]
    assert comparison["wins"] == [0]
    assert comparison["losses"] == [1]
    assert comparison["same_correct"] == [2]
    assert comparison["same_wrong"] == []
    assert comparison["final_line_wins"] == [0]
    assert comparison["final_line_losses"] == [1]
    assert comparison["missing_from_baseline"] == [4]
    assert comparison["missing_from_candidate"] == [3]


def test_render_markdown_includes_summary_and_examples() -> None:
    baseline = {
        0: sample(0, exact_correct=False, final_line_is_answer=False, answer="41"),
        1: sample(1, exact_correct=True, final_line_is_answer=True, answer="42"),
    }
    candidate = {
        0: sample(0, exact_correct=True, final_line_is_answer=True, answer="42"),
        1: sample(1, exact_correct=False, final_line_is_answer=True, answer="41"),
    }
    comparison = compare_records(baseline, candidate)

    report = render_markdown(
        comparison=comparison,
        baseline=baseline,
        candidate=candidate,
        baseline_path=Path("base/samples.jsonl"),
        candidate_path=Path("cand/samples.jsonl"),
        baseline_label="base",
        candidate_label="cand",
        max_examples=5,
        completion_chars=80,
    )

    assert "# Sample Comparison" in report
    assert "- wins: 1 [0]" in report
    assert "- losses: 1 [1]" in report
    assert "## Wins" in report
    assert "## Losses" in report
    assert "- base answer: `41` correct=False" in report
    assert "- cand answer: `42` correct=True" in report
