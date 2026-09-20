"""Safe dispatch from validated ActionAtoms to public ToolRegistry methods."""

from __future__ import annotations

from .action_validator import ActionValidator
from .models import ActionAtom
from .tool_schema import ToolSchema


class ToolDispatcher:
    def __init__(self, registry, schema: ToolSchema, validator: ActionValidator):
        self.registry = registry
        self.schema = schema
        self.validator = validator

    def dispatch(self, state, action: ActionAtom) -> dict:
        validation = self.validator.validate(action)
        if not validation.ok:
            raise ValueError("; ".join(validation.errors))
        if self.schema.get(action.tool) is None or action.tool.startswith("_"):
            raise ValueError(f"Tool is not dispatchable: {action.tool}")

        method = getattr(self.registry, action.tool, None)
        if not callable(method):
            raise ValueError(f"Tool is not callable: {action.tool}")
        return method(state, **action.args)
