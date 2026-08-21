from __future__ import annotations

import json

from ..infrastructure.llm import MockProvider
from .prompts import NARRATOR_SYSTEM


class Narrator:
    def __init__(self, assets, llm, constitution=None):
        self.assets = assets
        self.llm = llm
        self.constitution = constitution

    def render(self, *, old_state, intent, outcome, new_state):
        if isinstance(self.llm, MockProvider):
            return self._fallback(intent, outcome)

        payload = {
            "intent": intent.to_dict(),
            "resolved_outcome": outcome.to_dict(),
            "scene": {
                "name": self.assets.scene()["name"],
                "player_location": new_state["player"]["location"],
                "recent_events": new_state.get("events", [])[-5:],
            },
        }

        try:
            text = self.llm.text(
                system=NARRATOR_SYSTEM + ("\n\nL0 WORLD CONSTITUTION:\n" + self.constitution.llm_guardrails if self.constitution else ""),
                user=json.dumps(payload, ensure_ascii=False, indent=2),
                temperature=0.65,
            )
            return text.strip() or self._fallback(intent, outcome)
        except Exception:
            return self._fallback(intent, outcome)

    def _fallback(self, intent, outcome):
        chunks = [outcome.message]

        if outcome.npc_proposal:
            p = outcome.npc_proposal
            if p.get("action"):
                chunks.append(p["action"])
            if p.get("speech"):
                chunks.append(p["speech"])

        if outcome.rejected_claims:
            chunks.append("【边界】" + "；".join(outcome.rejected_claims))

        return "\n".join(x for x in chunks if x)
