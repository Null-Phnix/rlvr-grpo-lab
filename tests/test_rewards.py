from rlvr_lab.rewards import (
    answer_contract_progress_reward,
    answer_marker_correctness_reward,
    conversation_leak_penalty,
    extract_answer,
    extract_final_line_answer,
    extract_marked_answer,
    final_format_reward,
    final_line_correctness_reward,
    final_line_format_reward,
    has_role_label,
    has_text_after_final_marker,
    math_correctness_reward,
    normalize_answer,
    trailing_text_penalty,
)


def test_extract_answer_prefers_final_marker() -> None:
    assert extract_answer("scratch says 40. final says #### 42") == "42"


def test_extract_answer_supports_boxed_fallback() -> None:
    assert extract_answer(r"therefore \boxed{12}") == "12"


def test_extract_marked_answer_only_reads_hash_marker() -> None:
    assert extract_marked_answer("scratch 40\n#### 42\nextra 99") == "42"
    assert extract_marked_answer(r"therefore \boxed{12}") is None


def test_normalize_numeric_answer() -> None:
    assert normalize_answer("1,200.00") == "1200"


def test_math_correctness_reward() -> None:
    rewards = math_correctness_reward(
        completions=["reasoning #### 42", "bad #### 41"],
        ground_truth=["42", "42"],
    )
    assert rewards == [1.0, 0.0]


def test_final_line_correctness_reward_requires_correct_final_line() -> None:
    rewards = final_line_correctness_reward(
        completions=[
            "reasoning\n#### 42",
            "early #### 42\nthen extra",
            "reasoning\n#### 41",
        ],
        ground_truth=["42", "42", "42"],
    )
    assert rewards == [1.0, 0.0, 0.0]


def test_answer_marker_correctness_reward_ignores_trailing_text() -> None:
    rewards = answer_marker_correctness_reward(
        completions=[
            "reasoning\n#### 42\nHuman: keep going",
            "reasoning\n#### 41",
            "answer is 42",
        ],
        ground_truth=["42", "42", "42"],
    )
    assert rewards == [1.0, 0.0, 0.0]


def test_answer_contract_progress_reward_is_dense_but_correctness_anchored() -> None:
    rewards = answer_contract_progress_reward(
        completions=[
            "reasoning\n#### 42",
            "reasoning\n#### 42\nmore text",
            "reasoning\n#### 42\nHuman: keep going",
            "reasoning\n#### 41",
            "answer is 42",
        ],
        ground_truth=["42", "42", "42", "42", "42"],
    )
    assert rewards == [1.0, 0.75, 0.65, 0.15, 0.0]


def test_final_format_reward() -> None:
    assert final_format_reward(["reasoning #### 42", "answer is 42"]) == [1.0, 0.0]


def test_extract_final_line_answer_requires_last_line() -> None:
    assert extract_final_line_answer("work\n#### 42") == "42"
    assert extract_final_line_answer("work\n#### 42\nextra") is None


def test_has_text_after_final_marker() -> None:
    assert has_text_after_final_marker("work\n#### 42\nextra") is True
    assert has_text_after_final_marker("work\n#### 42") is False
    assert has_text_after_final_marker("work only") is False


def test_has_role_label_detects_conversation_continuations() -> None:
    assert has_role_label("work\n#### 42\nHuman: solve it again") is True
    assert has_role_label("assistantship is not a role label") is False


def test_final_line_format_reward() -> None:
    assert final_line_format_reward(["work\n#### 42", "work\n#### 42\nextra"]) == [1.0, 0.0]


def test_trailing_text_penalty() -> None:
    assert trailing_text_penalty(["work\n#### 42", "work\n#### 42\nextra"]) == [0.0, -1.0]


def test_conversation_leak_penalty() -> None:
    assert conversation_leak_penalty(["work\n#### 42", "work\n#### 42\nHuman: retry"]) == [
        0.0,
        -1.0,
    ]
