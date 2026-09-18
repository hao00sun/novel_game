from __future__ import annotations

from numbers import Real
from typing import Any, Iterable

from .models import SkillDefinition, SkillEvaluation


MIN_STAT = 1
MAX_STAT = 8
MIN_SKILL_LEVEL = 0
MAX_SKILL_LEVEL = 5
SKILL_WEIGHT = 0.7
STAT_WEIGHT = 0.3
POOR_MARGIN = -1.0
COMPETENT_MARGIN = 0.0
STRONG_MARGIN = 1.0


class CharacterSkillSystem:
    """Pure, deterministic competence calculation for Player and NPC actors."""

    def __init__(self, definitions: Iterable[SkillDefinition | dict[str, Any]]):
        self._definitions: dict[str, SkillDefinition] = {}
        for raw_definition in definitions:
            definition = (
                raw_definition
                if isinstance(raw_definition, SkillDefinition)
                else SkillDefinition.from_asset(raw_definition)
            )
            if definition.id in self._definitions:
                raise ValueError(f"Duplicate skill definition: {definition.id}")
            self._definitions[definition.id] = definition

    def get_definition(self, skill_id: str) -> SkillDefinition:
        try:
            return self._definitions[skill_id]
        except KeyError as error:
            raise ValueError(f"Unknown skill: {skill_id}") from error

    def evaluate(
        self,
        actor: dict[str, Any],
        skill_id: str,
        difficulty: float,
        context_modifiers: dict[str, float] | None = None,
    ) -> SkillEvaluation:
        definition = self.get_definition(skill_id)
        if not isinstance(difficulty, Real) or isinstance(difficulty, bool):
            raise ValueError("Skill difficulty must be numeric.")

        level = actor.get("skills", {}).get(skill_id, MIN_SKILL_LEVEL)
        if not isinstance(level, int) or isinstance(level, bool) or not MIN_SKILL_LEVEL <= level <= MAX_SKILL_LEVEL:
            raise ValueError(f"{skill_id} skill level must be an integer from 0 to 5.")

        modifiers = self._normalize_modifiers(context_modifiers)
        if definition.trained_only and level == MIN_SKILL_LEVEL:
            effective_score = 0.0
            margin = effective_score - float(difficulty)
            grade = "blocked"
        else:
            normalized_stat = self._normalized_related_stat(actor, definition)
            effective_score = (
                SKILL_WEIGHT * level
                + STAT_WEIGHT * normalized_stat
                + sum(modifiers.values())
            )
            margin = effective_score - float(difficulty)
            grade = self._grade_for_margin(margin)

        return SkillEvaluation(
            actor_id=actor.get("id", "unknown_actor"),
            skill_id=skill_id,
            level=level,
            effective_score=effective_score,
            difficulty=float(difficulty),
            margin=margin,
            grade=grade,
            modifiers=modifiers,
        )

    @staticmethod
    def _normalize_modifiers(
        context_modifiers: dict[str, float] | None,
    ) -> dict[str, float]:
        if context_modifiers is None:
            return {}
        modifiers = {}
        for name, value in context_modifiers.items():
            if not isinstance(value, Real) or isinstance(value, bool):
                raise ValueError(f"Context modifier {name} must be numeric.")
            modifiers[str(name)] = float(value)
        return modifiers

    @staticmethod
    def _grade_for_margin(margin: float) -> str:
        if margin < POOR_MARGIN:
            return "poor"
        if margin < COMPETENT_MARGIN:
            return "uncertain"
        if margin < STRONG_MARGIN:
            return "competent"
        return "strong"

    @staticmethod
    def _normalized_related_stat(
        actor: dict[str, Any], definition: SkillDefinition,
    ) -> float:
        stats = actor.get("stats", {})
        weighted_stat = 0.0
        for stat_id, weight in definition.related_stats.items():
            value = stats.get(stat_id)
            if not isinstance(value, Real) or isinstance(value, bool):
                raise ValueError(f"Actor is missing numeric stat: {stat_id}")
            weighted_stat += value * weight
        return (weighted_stat - MIN_STAT) / (MAX_STAT - MIN_STAT) * MAX_SKILL_LEVEL
