from rlvr_lab.datasets import gsm8k_gold_answer, make_prompt, prepare_gsm8k_row


def test_gsm8k_gold_answer_extracts_final_marker() -> None:
    assert gsm8k_gold_answer("work work\n#### 42") == "42"


def test_prepare_gsm8k_row_normalizes_prompt_and_ground_truth() -> None:
    row = {"question": "What is 40 + 2?", "answer": "40 + 2 = 42\n#### 42"}
    prepared = prepare_gsm8k_row(row)
    assert "What is 40 + 2?" in prepared["prompt"]
    assert prepared["ground_truth"] == "42"


def test_make_prompt_supports_answer_first() -> None:
    prompt = make_prompt("What is 40 + 2?", prompt_style="answer_first")
    assert "four hash marks" in prompt
    assert "What is 40 + 2?" in prompt


def test_make_prompt_supports_strict_final_line() -> None:
    prompt = make_prompt("What is 40 + 2?", prompt_style="strict_final_line")
    assert "last non-empty line" in prompt
    assert "#### 42" in prompt
    assert "Do not write anything after it." in prompt
    assert "What is 40 + 2?" in prompt


def test_make_prompt_supports_final_only() -> None:
    prompt = make_prompt("What is 40 + 2?", prompt_style="final_only")
    assert "Output exactly one line" in prompt
    assert "#### 42" in prompt
    assert "What is 40 + 2?" in prompt


def test_prompt_styles_do_not_use_angle_bracket_placeholders() -> None:
    for style in ["think_answer", "answer_first", "strict_final_line", "final_only"]:
        assert "<number>" not in make_prompt("What is 40 + 2?", prompt_style=style)
        assert "<answer>" not in make_prompt("What is 40 + 2?", prompt_style=style)


def test_make_prompt_rejects_unknown_style() -> None:
    try:
        make_prompt("2+2?", prompt_style="nope")
    except ValueError as exc:
        assert "unknown prompt_style" in str(exc)
    else:
        raise AssertionError("expected ValueError")
