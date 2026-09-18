from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SkillDefinition:
    """Persistent L2 definition of one composable character skill."""

    id: str
    name: str
    category: str
    applicable_tools: tuple[str, ...]
    related_stats: dict[str, float]
    trained_only: bool = False
    knowledge_domains: tuple[str, ...] = ()
    effects: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_asset(cls, data: dict[str, Any]) -> "SkillDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            applicable_tools=tuple(data.get("applicable_tools", [])),
            related_stats=dict(data["related_stats"]),
            trained_only=bool(data.get("trained_only", False)),
            knowledge_domains=tuple(data.get("knowledge_domains", [])),
            effects=dict(data.get("effects", {})),
        )


@dataclass(frozen=True)
class SkillEvaluation:
    """L4 competence calculation; it is not a World State change."""

    actor_id: str
    skill_id: str
    level: int
    effective_score: float
    difficulty: float
    margin: float
    grade: str
    modifiers: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
