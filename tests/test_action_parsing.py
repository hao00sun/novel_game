import json
import unittest
from copy import deepcopy
from pathlib import Path

from novel_world.agents.intent import IntentAgent
from novel_world.assets.loader import AssetLoader
from novel_world.world.action_validator import ActionValidator
from novel_world.world.tool_schema import ToolSchema
from novel_world.world.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


class StubActionProvider:
    provider_name = "stub"

    def __init__(self, response):
        self.response = response
        self.payload = None

    def json(self, *, system, user, temperature=0.2):
        self.payload = json.loads(user)
        return self.response


class ActionParsingTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ROOT / "assets" / "beginner_world")
        self.schema = ToolSchema.from_registry(ToolRegistry(self.assets))
        self.validator = ActionValidator(self.schema)

    def state_at(self, location):
        entities = {
            entity["id"]: deepcopy(entity)
            for entity in self.assets.objects()
        }
        for entity in entities.values():
            entity.setdefault("holder", None)
            entity.setdefault("contained_in", None)
        return {
            "player": {"id": "lu_chen", "location": location, "held_items": []},
            "actors": {},
            "entities": entities,
        }

    def parse(self, text, response, state):
        provider = StubActionProvider(response)
        agent = IntentAgent(
            self.assets,
            provider,
            action_schema=self.schema,
            action_validator=self.validator,
        )
        return agent.interpret_actions(text, state), provider.payload

    def test_inspect_candidate_is_valid_and_schema_is_sent_to_llm(self):
        bundle, payload = self.parse(
            "观察一下周围",
            {"actions": [{"tool": "inspect", "args": {}}], "ambiguities": []},
            self.state_at("forest"),
        )
        self.assertEqual([action.tool for action in bundle.actions], ["inspect"])
        take_definition = next(item for item in payload["tool_schema"] if item["name"] == "take")
        self.assertEqual(take_definition["required_args"], ["object_id"])
        self.assertIn("fallen_branch", {item["id"] for item in payload["reference_context"]["entities"]})

    def test_take_visible_entity_uses_its_runtime_id(self):
        bundle, _ = self.parse(
            "拿起枯木枝",
            {"actions": [{"tool": "take", "args": {"object_id": "fallen_branch"}}]},
            self.state_at("forest"),
        )
        self.assertEqual(bundle.actions[0].args["object_id"], "fallen_branch")

    def test_open_visible_container(self):
        bundle, _ = self.parse(
            "打开客栈木箱",
            {"actions": [{"tool": "open", "args": {"target_id": "inn_wooden_box"}}]},
            self.state_at("inn"),
        )
        self.assertEqual(bundle.actions[0].tool, "open")

    def test_declared_multi_actions_preserve_order(self):
        bundle, _ = self.parse(
            "拿起枯木枝，然后观察它",
            {
                "actions": [
                    {"tool": "take", "args": {"object_id": "fallen_branch"}},
                    {"tool": "inspect", "args": {"target": "fallen_branch"}},
                ]
            },
            self.state_at("forest"),
        )
        self.assertEqual([action.tool for action in bundle.actions], ["take", "inspect"])

    def test_unknown_tool_or_argument_is_rejected_by_action_validator(self):
        for response in [
            {"actions": [{"tool": "teleport", "args": {"destination_id": "forest"}}]},
            {"actions": [{"tool": "take", "args": {"foo": "fallen_branch"}}]},
            {"actions": [{"tool": "tracking", "args": {}}]},
        ]:
            bundle, _ = self.parse("测试", response, self.state_at("forest"))
            self.assertEqual(bundle.actions, [])
            self.assertTrue(bundle.ambiguities)

    def test_unknown_entity_id_is_rejected_by_reference_validation(self):
        bundle, _ = self.parse(
            "拿起宝剑",
            {"actions": [{"tool": "take", "args": {"object_id": "dragon_sword_001"}}]},
            self.state_at("forest"),
        )
        self.assertEqual(bundle.actions, [])
        self.assertIn("Unknown reference", bundle.ambiguities[0])


if __name__ == "__main__":
    unittest.main()
