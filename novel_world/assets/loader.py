from __future__ import annotations

from collections import deque
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
        self._validate_skill_assets()

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

    def skills_bundle(self):
        return self._load("skills.json")

    def skills(self):
        return self.skills_bundle()["skills"]

    def get_skill(self, skill_id: str):
        for skill in self.skills():
            if skill["id"] == skill_id:
                return skill
        raise KeyError(f"Unknown skill: {skill_id}")

    def objects(self):
        return self._load("objects.json")["objects"]

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

    def _validate_skill_assets(self):
        stat_keys = {"physique", "agility", "intellect", "perception", "social", "will"}
        skill_ids = set()
        for skill in self.skills():
            skill_id = skill.get("id")
            if not skill_id or skill_id in skill_ids:
                raise ValueError(f"Duplicate or missing skill id: {skill_id}")
            skill_ids.add(skill_id)
            unknown_stats = set(skill.get("related_stats", {})) - stat_keys
            if unknown_stats:
                raise ValueError(f"Skill {skill_id} uses unknown stats: {sorted(unknown_stats)}")

        for character in self.characters():
            skills = character.get("skills", {})
            if not isinstance(skills, dict):
                raise ValueError(f"Character {character['id']} skills must be an object.")
            for skill_id, level in skills.items():
                if skill_id not in skill_ids:
                    raise ValueError(f"Character {character['id']} uses unknown skill: {skill_id}")
                if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 5:
                    raise ValueError(f"Character {character['id']} skill {skill_id} must be 0~5.")

    def is_location_reachable(self, source_id: str, destination_id: str) -> bool:
        """Return whether the static L2 location graph contains a route."""
        locations = {location["id"]: location for location in self.locations()}
        if source_id not in locations or destination_id not in locations:
            return False

        pending = deque([source_id])
        visited = {source_id}
        while pending:
            current_id = pending.popleft()
            if current_id == destination_id:
                return True

            for next_id in locations[current_id].get("connections", []):
                if next_id not in locations:
                    raise ValueError(
                        f"Location {current_id} references unknown connection {next_id}."
                    )
                if next_id not in visited:
                    visited.add(next_id)
                    pending.append(next_id)
        return False

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
