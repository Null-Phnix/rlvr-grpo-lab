from rlvr_lab.postprocess import (
    cut_at_first_stop,
    postprocess_completion,
    postprocess_completions,
    truncate_after_final_marker,
)


def test_cut_at_first_stop_uses_earliest_match() -> None:
    text = "work\n#### 42\nUser: retry\nHuman: retry"

    assert cut_at_first_stop(text, ["\nHuman:", "\nUser:"]) == "work\n#### 42"


def test_cut_at_first_stop_ignores_missing_or_empty_stops() -> None:
    text = "work\n#### 42"

    assert cut_at_first_stop(text, ["", "\nHuman:"]) == text


def test_truncate_after_final_marker_keeps_only_marker_answer() -> None:
    assert truncate_after_final_marker("work\n#### 42. Do not continue") == "work\n#### 42"


def test_postprocess_completion_combines_stop_and_final_marker_truncation() -> None:
    completion = "work\n#### 42\nHuman: retry"
    config = {
        "stop_sequences": ["\nHuman:"],
        "truncate_after_final_marker": True,
    }

    assert postprocess_completion(completion, config) == "work\n#### 42"


def test_postprocess_completions() -> None:
    assert postprocess_completions(
        ["work\n#### 42\nHuman: retry"],
        {"stop_sequences": ["\nHuman:"]},
    ) == ["work\n#### 42"]
