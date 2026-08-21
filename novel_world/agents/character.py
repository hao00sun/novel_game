from __future__ import annotations

import json

from ..infrastructure.llm import MockProvider
from ..world.models import CharacterProposal
from .prompts import CHARACTER_SYSTEM


class CharacterAgent:
    def __init__(self, assets, llm, constitution=None):
        self.assets = assets
        self.llm = llm
        self.constitution = constitution

    def react(self, actor_id: str, state: dict, intent) -> CharacterProposal:
        actor_asset = self.assets.get_character(actor_id)
        runtime_actor = state.get("actors", {}).get(actor_id, {})
        profile = actor_asset.get("agent_profile", {})

        if isinstance(self.llm, MockProvider):
            return self._fallback(actor_asset, intent)

        # Character Agent receives only world context relevant to the character.
        payload = {
            "character": {
                "id": actor_id,
                "name": actor_asset["name"],
                "identity": actor_asset["identity"],
                "role": profile.get("role", []),
                "goals": runtime_actor.get("goals", profile.get("goals", [])),
                "beliefs": runtime_actor.get("beliefs", profile.get("beliefs", [])),
                "emotion": runtime_actor.get("emotion", profile.get("emotion", {})),
                "norms": profile.get("norms", []),
                "knowledge": profile.get("knowledge", []),
                "relationship_context": runtime_actor.get(
                    "relationship_context",
                    profile.get("relationship_context", [])
                ),
            },
            "situation": {
                "location": state["player"]["location"],
                "player": {
                    "name": state["player"]["name"],
                    "identity": state["player"]["identity"],
                },
                "player_intent": intent.to_dict(),
                "recent_events": state.get("events", [])[-6:],
            },
        }

        try:
            data = self.llm.json(
                system=CHARACTER_SYSTEM + ("\n\nL0 WORLD CONSTITUTION:\n" + self.constitution.llm_guardrails if self.constitution else ""),
                user=json.dumps(payload, ensure_ascii=False, indent=2),
                temperature=0.5,
            )
            return CharacterProposal(
                actor_id=actor_id,
                intent=str(data.get("intent", "观察玩家")),
                speech=str(data.get("speech", "")),
                action=str(data.get("action", "保持当前行为")),
                desired_outcome=data.get("desired_outcome"),
                belief_update_candidate=data.get("belief_update_candidate"),
                emotion_update_candidate=data.get("emotion_update_candidate"),
                reasoning_summary=str(data.get("reasoning_summary", "")),
            )
        except Exception:
            return self._fallback(actor_asset, intent)

    def _fallback(self, actor_asset, intent) -> CharacterProposal:
        name = actor_asset["name"]
        identity = actor_asset["identity"]

        if intent.kind == "talk":
            return CharacterProposal(
                actor_id=actor_asset["id"],
                intent="谨慎回应陌生人的搭话",
                speech=f"“你找我有什么事？”",
                action=f"{name}暂时停下手头的事，看向你。",
                desired_outcome="弄清玩家来意",
                reasoning_summary=f"{identity}对突然搭话保持普通程度的谨慎。",
            )

        return CharacterProposal(
            actor_id=actor_asset["id"],
            intent="观察",
            speech="",
            action=f"{name}没有明显反应。",
            reasoning_summary="当前没有需要主动回应的行为。",
        )
