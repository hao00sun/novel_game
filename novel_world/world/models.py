from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class Intent:
    kind: str
    raw_text: str
    target: str | None = None
    destination: str | None = None
    speech: str | None = None
    desired_outcome: str | None = None
    extraordinary: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class CharacterProposal:
    actor_id: str
    intent: str
    speech: str
    action: str
    desired_outcome: str | None = None
    belief_update_candidate: str | None = None
    emotion_update_candidate: str | None = None
    reasoning_summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Outcome:
    ok: bool
    message: str
    state_changes: list[dict[str, Any]] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    npc_proposal: dict[str, Any] | None = None
    rejected_claims: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
