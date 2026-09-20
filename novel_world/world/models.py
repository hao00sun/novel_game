'''
本文件决定各组件之间用什么格式传递信息。
1、可能传递的信息不够丰富？
2、可能数据接口种类不够？
3、“裁决”有些可能不是单纯的bool决定
4、当前的event不够用
5、没有time模型


'''

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
class ActionAtom:
    """One player-declared candidate Tool call; it has no State authority."""

    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    desired_outcome: str | None = None
    raw_text: str | None = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ActionBundle:
    """Ordered decomposition of only the actions stated by the player."""

    raw_text: str
    actions: list[ActionAtom]
    ambiguities: list[str] = field(default_factory=list)

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
    skill_checks: list[dict[str, Any]] = field(default_factory=list)
    action_results: list[dict[str, Any]] = field(default_factory=list)
    unresolved_requests: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
