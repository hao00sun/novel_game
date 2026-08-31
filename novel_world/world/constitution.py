'''
确保L0不被改变

后续发展继续保持：宪法的注册、读取、版本、兼容性、原则声明与校验入口

'''

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WorldConstitution:
    """
    L0 immutable rules.
    Runtime modules may read this layer but may not mutate it.
    """

    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)
        self._manifest = self._load_manifest()
        self._skill_text = self._load_skill_text()

    def _load_manifest(self) -> dict[str, Any]:
        path = self.skill_dir / "manifest.json"
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("layer") != "L0":
            raise ValueError("World Constitution 必须属于 L0。")
        if data.get("mutability") != "immutable":
            raise ValueError("World Constitution 必须标记为 immutable。")
        return data

    def _load_skill_text(self) -> str:
        return (self.skill_dir / "SKILL.md").read_text(encoding="utf-8")

    @property
    def manifest(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._manifest))

    @property
    def skill_text(self) -> str:
        return str(self._skill_text)

    @property
    def llm_guardrails(self) -> str:
        rules = self._manifest.get("llm_guardrails", [])
        return "\n".join(f"- {x}" for x in rules)

    def assert_world_compatible(self, world_asset: dict[str, Any]) -> None:
        required = world_asset.get("constitution", {})
        if required.get("required") is not True:
            raise ValueError("该世界没有声明必须使用 World Constitution。")
        if required.get("skill_id") != self._manifest["skill_id"]:
            raise ValueError("世界声明的 constitution skill_id 与当前 L0 不匹配。")
