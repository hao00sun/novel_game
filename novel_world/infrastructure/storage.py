from __future__ import annotations

import json
from pathlib import Path


class JsonStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def exists(self):
        return self.path.exists()

    def save(self, state):
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        temp.replace(self.path)

    def load(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def delete(self):
        if self.path.exists():
            self.path.unlink()
