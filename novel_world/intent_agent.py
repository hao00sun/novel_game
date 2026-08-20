from __future__ import annotations

import json

from .llm import MockProvider
from .models import Intent
from .prompts import INTENT_SYSTEM


EXTRAORDINARY_WORDS = [
    "轻功", "御剑", "法术", "内力", "真气", "飞行",
    "瞬移", "读心", "隐身", "妖术", "神通", "灵力"
]


class IntentAgent:
    def __init__(self, assets, llm, constitution=None):
        self.assets = assets
        self.llm = llm
        self.constitution = constitution

    def interpret(self, text: str, state: dict) -> Intent:
        if isinstance(self.llm, MockProvider):
            return self._fallback(text)

        locations = [
            {"id": x["id"], "name": x["name"], "aliases": x.get("aliases", [])}
            for x in self.assets.locations()
        ]
        characters = [
            {"id": x["id"], "name": x["name"], "identity": x["identity"]}
            for x in self.assets.characters()
        ]

        payload = {
            "player_text": text,
            "current_location": state["player"]["location"],
            "known_locations": locations,
            "known_characters": characters,
            "extraordinary_enabled": self.assets.world()["extraordinary"]["enabled"],
        }

        try:
            data = self.llm.json(
                system=INTENT_SYSTEM + ("\n\nL0 WORLD CONSTITUTION:\n" + self.constitution.llm_guardrails if self.constitution else ""),
                user=json.dumps(payload, ensure_ascii=False, indent=2),
                temperature=0.1,
            )
            return Intent(
                kind=str(data.get("kind", "freeform")),
                raw_text=text,
                target=data.get("target"),
                destination=data.get("destination"),
                speech=data.get("speech"),
                desired_outcome=data.get("desired_outcome"),
                extraordinary=bool(data.get("extraordinary", False)),
            )
        except Exception:
            # API 格式失败时，降级到规则解释，世界仍可运行。
            return self._fallback(text)

    def _fallback(self, text: str) -> Intent:
        t = text.strip()
        extraordinary = any(word in t for word in EXTRAORDINARY_WORDS)

        loc = self.assets.find_location_by_name(t)
        char = self.assets.find_character_by_name(t)

        if extraordinary:
            return Intent(
                kind="extraordinary",
                raw_text=t,
                extraordinary=True,
                target=char["id"] if char else None,
            )

        if char and loc and any(k in t for k in ["说", "问", "聊", "交谈", "打听", "告诉"]):
            return Intent(
                kind="talk",
                raw_text=t,
                target=char["id"],
                destination=loc["id"],
                speech=t,
            )

        if loc and any(k in t for k in ["去", "前往", "走到", "来到"]):
            return Intent(
                kind="move",
                raw_text=t,
                destination=loc["id"],
            )

        if char and any(k in t for k in ["说", "问", "聊", "交谈", "打听", "告诉"]):
            return Intent(
                kind="talk",
                raw_text=t,
                target=char["id"],
                speech=t,
            )

        if any(k in t for k in ["看看", "查看", "观察", "四周", "这里"]):
            return Intent(kind="inspect", raw_text=t)

        return Intent(kind="freeform", raw_text=t)
