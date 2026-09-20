import unittest
from pathlib import Path

from novel_world.assets.loader import AssetLoader
from novel_world.world.action_validator import ActionValidator
from novel_world.world.models import ActionAtom, ActionBundle
from novel_world.world.tool_schema import ToolSchema
from novel_world.world.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


class ActionSystemTests(unittest.TestCase):
    def setUp(self):
        assets = AssetLoader(ROOT / "assets" / "beginner_world")
        self.schema = ToolSchema.from_registry(ToolRegistry(assets))
        self.validator = ActionValidator(self.schema)

    def test_action_atom_serializes(self):
        action = ActionAtom("take", {"object_id": "blank_paper"}, "获得纸页", "拿起纸")
        self.assertEqual(action.to_dict()["args"]["object_id"], "blank_paper")
        self.assertEqual(action.to_dict()["desired_outcome"], "获得纸页")

    def test_action_bundle_preserves_declared_order(self):
        bundle = ActionBundle(
            raw_text="先看告示再读它",
            actions=[
                ActionAtom("look", {"target": "east_gate_notice"}),
                ActionAtom("read", {"target_id": "east_gate_notice"}),
            ],
        )
        self.assertEqual([action.tool for action in bundle.actions], ["look", "read"])

    def test_schema_uses_current_tool_signatures(self):
        self.assertEqual(self.schema.get("take").required_args, ("object_id",))
        self.assertEqual(self.schema.get("move").optional_args, ("manner",))
        self.assertIn("strike", self.schema.names())

    def test_legal_tool_call_is_valid(self):
        result = self.validator.validate(ActionAtom("take", {"object_id": "blank_paper"}))
        self.assertTrue(result.ok)

    def test_unknown_tool_is_invalid(self):
        result = self.validator.validate(ActionAtom("teleport", {"destination": "forest"}))
        self.assertFalse(result.ok)
        self.assertIn("Unknown tool", result.errors[0])

    def test_missing_required_argument_is_invalid(self):
        result = self.validator.validate(ActionAtom("take", {}))
        self.assertFalse(result.ok)
        self.assertIn("Missing required", result.errors[0])

    def test_unknown_argument_is_invalid(self):
        result = self.validator.validate(ActionAtom("take", {"foo": "bar"}))
        self.assertFalse(result.ok)
        self.assertIn("Unknown arguments", result.errors[0])


if __name__ == "__main__":
    unittest.main()
