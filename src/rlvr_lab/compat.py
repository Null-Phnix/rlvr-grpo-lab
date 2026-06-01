from __future__ import annotations

import warnings
from collections.abc import Collection, Mapping
from typing import Any


def filter_supported_kwargs(
    requested_kwargs: Mapping[str, Any],
    supported_kwargs: Collection[str],
    *,
    owner: str,
) -> dict[str, Any]:
    supported = set(supported_kwargs)
    dropped = sorted(set(requested_kwargs) - supported)
    if dropped:
        warnings.warn(
            f"{owner} does not support these requested config keys; ignoring: "
            f"{', '.join(dropped)}",
            RuntimeWarning,
            stacklevel=2,
        )
    return {
        name: value
        for name, value in requested_kwargs.items()
        if name in supported
    }
