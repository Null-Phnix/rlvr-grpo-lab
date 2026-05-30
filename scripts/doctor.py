from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys

from rich.console import Console
from rich.table import Table


def _version(module: str) -> str:
    spec = importlib.util.find_spec(module)
    if spec is None:
        return "not installed"
    mod = __import__(module)
    return getattr(mod, "__version__", "installed")


def _nvidia_smi() -> str:
    if shutil.which("nvidia-smi") is None:
        return "not found"
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or result.stderr.strip()


def main() -> None:
    table = Table(title="RLVR GRPO Lab Doctor")
    table.add_column("Check")
    table.add_column("Value")

    table.add_row("python", sys.version.split()[0])
    table.add_row("platform", platform.platform())
    table.add_row("nvidia", _nvidia_smi())
    table.add_row("torch", _version("torch"))
    table.add_row("transformers", _version("transformers"))
    table.add_row("trl", _version("trl")
)
    table.add_row("datasets", _version("datasets"))
    table.add_row("peft", _version("peft"))
    table.add_row("bitsandbytes", _version("bitsandbytes"))

    Console().print(table)


if __name__ == "__main__":
    main()
