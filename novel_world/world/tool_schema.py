"""Tool call shapes derived from the public ToolRegistry method signatures."""

from __future__ import annotations

import inspect
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    required_args: tuple[str, ...]
    optional_args: tuple[str, ...]

    @property
    def accepted_args(self) -> tuple[str, ...]:
        return (*self.required_args, *self.optional_args)


class ToolSchema:
    """Read-only schema for the public candidate-action methods of one registry."""

    def __init__(self, definitions: dict[str, ToolDefinition]):
        self._definitions = definitions

    @classmethod
    def from_registry(cls, registry) -> "ToolSchema":
        definitions = {}
        for name, method in inspect.getmembers(registry, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue

            required_args = []
            optional_args = []
            for parameter in inspect.signature(method).parameters.values():
                if parameter.name == "state":
                    continue
                if parameter.kind not in {
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                }:
                    raise TypeError(f"Tool {name} has unsupported parameter: {parameter.name}")
                target = required_args if parameter.default is inspect.Parameter.empty else optional_args
                target.append(parameter.name)

            definitions[name] = ToolDefinition(
                name=name,
                required_args=tuple(required_args),
                optional_args=tuple(optional_args),
            )
        return cls(definitions)

    def get(self, tool_name: str) -> ToolDefinition | None:
        return self._definitions.get(tool_name)

    def names(self) -> tuple[str, ...]:
        return tuple(self._definitions)

    def to_prompt_data(self) -> list[dict[str, object]]:
        """Return the schema in the compact, JSON-safe form used by Action parsing."""
        return [
            {
                "name": definition.name,
                "required_args": list(definition.required_args),
                "optional_args": list(definition.optional_args),
            }
            for definition in self._definitions.values()
        ]
