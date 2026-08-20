from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | Path) -> None:
    """
    Minimal .env reader. Existing environment variables always win.
    """
    path = Path(path)
    if not path.exists():
        return

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
