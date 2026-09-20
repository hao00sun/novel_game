"""Structural validation for candidate Tool calls; no world resolution occurs here."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import ActionAtom
from .tool_schema import ToolSchema


@dataclass(frozen=True)
class ActionValidationResult:
    action: ActionAtom
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class ActionValidator:
    """Validate only that an ActionAtom has a known, structurally valid Tool call."""

    def __init__(self, schema: ToolSchema):
        self.schema = schema

    def validate(self, action: ActionAtom) -> ActionValidationResult:
        definition = self.schema.get(action.tool)
        if definition is None:
            return ActionValidationResult(action, [f"Unknown tool: {action.tool}"])
        if not isinstance(action.args, dict):
            return ActionValidationResult(action, ["Action args must be a dictionary."])

        errors = []
        unknown_args = set(action.args) - set(definition.accepted_args)
        if unknown_args:
            errors.append(f"Unknown arguments for {action.tool}: {sorted(unknown_args)}")

        missing_args = [name for name in definition.required_args if name not in action.args]
        if missing_args:
            errors.append(f"Missing required arguments for {action.tool}: {missing_args}")

        return ActionValidationResult(action, errors)
