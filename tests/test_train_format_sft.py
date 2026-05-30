from rlvr_lab.train_format_sft import format_sft_completion, tokenize_prompt_completion


class FakeTokenizer:
    def __call__(self, text: str, add_special_tokens: bool = False) -> dict[str, list[int]]:
        return {"input_ids": [ord(char) for char in text]}


def test_format_sft_completion_adds_final_line_and_eos() -> None:
    assert format_sft_completion(" 42 ", "<eos>") == "\n#### 42<eos>"


def test_tokenize_prompt_completion_masks_prompt_tokens() -> None:
    tokenized = tokenize_prompt_completion(
        tokenizer=FakeTokenizer(),
        prompt="Question:",
        completion="\n#### 42",
        max_seq_length=128,
    )

    prompt_length = len("Question:")
    assert tokenized["input_ids"][:prompt_length] == [ord(char) for char in "Question:"]
    assert tokenized["labels"][:prompt_length] == [-100] * prompt_length
    assert tokenized["labels"][prompt_length:] == tokenized["input_ids"][prompt_length:]
