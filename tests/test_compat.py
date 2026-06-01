import pytest

from rlvr_lab.compat import filter_supported_kwargs


def test_filter_supported_kwargs_keeps_supported_values() -> None:
    filtered = filter_supported_kwargs(
        {"alpha": 1, "beta": 2},
        {"alpha", "beta"},
        owner="ExampleConfig",
    )

    assert filtered == {"alpha": 1, "beta": 2}


def test_filter_supported_kwargs_warns_about_dropped_values() -> None:
    with pytest.warns(RuntimeWarning, match="beta"):
        filtered = filter_supported_kwargs(
            {"alpha": 1, "beta": 2},
            {"alpha"},
            owner="ExampleConfig",
        )

    assert filtered == {"alpha": 1}
