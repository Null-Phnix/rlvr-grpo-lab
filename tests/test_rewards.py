from rlvr_lab.rewards import (
    extract_answer,
    extract_final_line_answer,
    final_format_reward,
    final_line_format_reward,
    has_text_after_final_marker,
    math_correctness_reward,
    normalize_answer,
    trailing_text_penalty,
)


def test_extract_answer_prefers_final_marker() -> None:
    assert extract_answer("scratch says 40. final says #### 42") == "42"


def test_extract_answer_supports_boxed_fallback() -> None:
    assert extract_answer(r"therefore \boxed{12}") == "12"


def test_normalize_numeric_answer() -> None:
    assert normalize_answer("1,200.00") == "1200"


def test_math_correctness_reward() -> None:
    rewards = math_correctness_reward(
        completions=["reasoning #### 42", "bad #### 41"],
        ground_truth=["42", "42"],
    )
    assert rewards == [1.0, 0.0]


def test_final_format_reward() -> None:
    assert final_format_reward(["reasoning #### 42", "answer is 42"]) == [1.0, 0.0]


def test_extract_final_line_answer_requires_last_line() -> None:
    assert extract_final_line_answer("work\n#### 42") == "42"
    assert extract_final_line_answer("work\n#### 42\nextra") is None


def test_has_text_after_final_marker() -> None:
    assert has_text_after_final_marker("work\n#### 42\nextra") is True
    assert has_text_after_final_marker("work\n#### 42") is False
    assert has_text_after_final_marker("work only") is False


def test_final_line_format_reward() -> None:
    assert final_line_format_reward(["work\n#### 42", "work\n#### 42\nextra"]) == [1.0, 0.0]


def test_trailing_text_penalty() -> None:
    assert trailing_text_penalty(["work\n#### 42", "work\n#### 42\nextra"]) == [0.0, -1.0]
