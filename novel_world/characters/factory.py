

from __future__ import annotations

from copy import deepcopy
from typing import Any


STAT_KEYS = [
    "physique",
    "agility",
    "intellect",
    "perception",
    "social",
    "will",
]


class CharacterFactory:
    def __init__(self, character_bundle: dict[str, Any]):
        self.bundle = character_bundle

    def from_preset(self, asset: dict[str, Any]) -> dict[str, Any]:
        if not asset.get("selectable"):
            raise ValueError("该角色不可被玩家选择。")
        if "官" in asset.get("identity_tags", []):
            raise ValueError("官身份角色不可被玩家选择。")

        runtime = deepcopy(asset)
        runtime["source"] = "preset"
        runtime["inventory"] = list(asset.get("assets", []))
        runtime["status"] = {"injured": False}
        return runtime

    def create_custom(
        self,
        name: str,
        identity: str,
        stats: dict[str, int],
        location: str,
    ) -> dict[str, Any]:
        cfg = self.bundle["custom_character"]

        if identity not in cfg["allowed_social_status"]:
            raise ValueError("该身份不在 v0.1 自建角色允许范围内。")

        if set(stats) != set(STAT_KEYS):
            raise ValueError("属性字段不完整。")

        for key, value in stats.items():
            if not isinstance(value, int):
                raise ValueError(f"{key} 必须是整数。")
            if value < cfg["min_each"] or value > cfg["max_each"]:
                raise ValueError(
                    f"{key} 必须位于 {cfg['min_each']}~{cfg['max_each']}。"
                )

        if sum(stats.values()) > cfg["stat_budget"]:
            raise ValueError(
                f"自建角色总属性不能超过 {cfg['stat_budget']}，当前为 {sum(stats.values())}。"
            )

        return {
            "id": "custom_player",
            "name": name,
            "identity": identity,
            "identity_tags": [identity],
            "selectable": True,
            "source": "custom",
            "location": location,
            "background": "玩家自建角色。背景在后续版本继续扩展。",
            "assets": [],
            "inventory": [],
            "skills": {},
            "stats": stats,
            "extraordinary_traits": [],
            "status": {"injured": False},
        }
