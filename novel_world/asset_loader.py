from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AssetLoader:
    """
    L1/L2 资产读取唯一入口。
    核心框架不 hard-code 某个具体世界。
    """

    def __init__(self, asset_dir: str | Path):
        self.asset_dir = Path(asset_dir)

    def _load(self, filename: str) -> dict[str, Any]:
        path = self.asset_dir / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def world(self):
        return self._load("world.json")

    def scene(self):
        return self._load("scene.json")

    def locations(self):
        return self._load("locations.json")["locations"]

    def characters_bundle(self):
        return self._load("characters.json")

    def characters(self):
        return self.characters_bundle()["characters"]

    def selectable_characters(self):
        return [c for c in self.characters() if c.get("selectable") is True]

    def get_character(self, character_id: str):
        for c in self.characters():
            if c["id"] == character_id:
                return c
        raise KeyError(f"Unknown character: {character_id}")

    def get_location(self, location_id: str):
        for loc in self.locations():
            if loc["id"] == location_id:
                return loc
        raise KeyError(f"Unknown location: {location_id}")

    def find_location_by_name(self, text: str):
        for loc in self.locations():
            candidates = [loc["name"], loc["id"], *loc.get("aliases", [])]
            if any(candidate and candidate in text for candidate in candidates):
                return loc
        return None

    def find_character_by_name(self, text: str):
        for c in self.characters():
            if c["name"] in text or c["id"] in text:
                return c
        return None
