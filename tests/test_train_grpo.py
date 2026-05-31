import pytest

from rlvr_lab.train_grpo import resolve_resume_from_checkpoint


def test_resolve_resume_from_checkpoint_defaults_to_none() -> None:
    assert resolve_resume_from_checkpoint({}) is None
    assert resolve_resume_from_checkpoint({"training": {}}) is None


def test_resolve_resume_from_checkpoint_ignores_disabled_values() -> None:
    assert resolve_resume_from_checkpoint({"training": {"resume_from_checkpoint": False}}) is None
    assert resolve_resume_from_checkpoint({"training": {"resume_from_checkpoint": ""}}) is None


def test_resolve_resume_from_checkpoint_allows_latest_checkpoint_flag() -> None:
    assert resolve_resume_from_checkpoint({"training": {"resume_from_checkpoint": True}}) is True


def test_resolve_resume_from_checkpoint_requires_existing_path(tmp_path) -> None:
    checkpoint = tmp_path / "checkpoint-100"
    checkpoint.mkdir()

    assert (
        resolve_resume_from_checkpoint({"training": {"resume_from_checkpoint": str(checkpoint)}})
        == str(checkpoint)
    )


def test_resolve_resume_from_checkpoint_rejects_missing_path(tmp_path) -> None:
    missing = tmp_path / "checkpoint-404"

    with pytest.raises(FileNotFoundError, match="resume checkpoint does not exist"):
        resolve_resume_from_checkpoint({"training": {"resume_from_checkpoint": str(missing)}})
