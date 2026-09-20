import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from novel_world.agents.character import CharacterAgent
from novel_world.agents.intent import IntentAgent
from novel_world.agents.narrator import Narrator
from novel_world.assets.loader import AssetLoader
from novel_world.characters.factory import CharacterFactory
from novel_world.characters.skills import CharacterSkillSystem
from novel_world.engine import GameEngine
from novel_world.infrastructure.llm import MockProvider
from novel_world.infrastructure.storage import JsonStore
from novel_world.world.action_validator import ActionValidator
from novel_world.world.constitution import WorldConstitution
from novel_world.world.models import ActionAtom, ActionBundle
from novel_world.world.resolver import WorldResolver
from novel_world.world.state_manager import StateManager
from novel_world.world.tool_dispatcher import ToolDispatcher
from novel_world.world.tool_schema import ToolSchema
from novel_world.world.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


class StubActionProvider:
    provider_name = "stub"

    def __init__(self, response):
        self.response = response

    def json(self, *, system, user, temperature=0.2):
        return self.response


class ActionExecutionTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ROOT / "assets" / "beginner_world")
        self.constitution = WorldConstitution(ROOT / "skills" / "world_core")

    def engine_for(self, response, location="forest"):
        tools = ToolRegistry(self.assets)
        schema = ToolSchema.from_registry(tools)
        validator = ActionValidator(schema)
        state_manager = StateManager()
        resolver = WorldResolver(
            self.assets,
            tools,
            CharacterSkillSystem(self.assets.skills()),
            action_dispatcher=ToolDispatcher(tools, schema, validator),
            state_manager=state_manager,
        )
        player = CharacterFactory(self.assets.characters_bundle()).from_preset(
            self.assets.get_character("lu_chen")
        )
        player["location"] = location
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        engine = GameEngine(
            constitution=self.constitution,
            assets=self.assets,
            intent_agent=IntentAgent(
                self.assets,
                StubActionProvider(response),
                self.constitution,
                action_schema=schema,
                action_validator=validator,
            ),
            character_agent=CharacterAgent(self.assets, MockProvider(), self.constitution),
            resolver=resolver,
            state_manager=state_manager,
            narrator=Narrator(self.assets, MockProvider(), self.constitution),
            store=JsonStore(Path(temp_dir.name) / "save.json"),
        )
        engine.create_state(player)
        return engine, resolver

    def test_take_executes_once_and_commits_through_engine(self):
        engine, _ = self.engine_for({
            "actions": [{"tool": "take", "args": {"object_id": "fallen_branch"}}]
        })

        intent, outcome, state, _ = engine.step("拿起枯木枝")

        self.assertTrue(outcome.ok)
        self.assertEqual(intent.kind, "action_bundle")
        self.assertEqual(state["turn"], 1)
        self.assertEqual(state["entities"]["fallen_branch"]["holder"], "lu_chen")
        self.assertEqual(state["player"]["inventory"].count("fallen_branch"), 1)
        self.assertEqual(len(outcome.action_results), 1)
        self.assertIsNotNone(state["history"][-1]["action_bundle"])

    def test_open_visible_container_executes(self):
        engine, _ = self.engine_for({
            "actions": [{"tool": "open", "args": {"target_id": "inn_wooden_box"}}]
        }, location="inn")

        _, outcome, state, _ = engine.step("打开客栈木箱")

        self.assertTrue(outcome.ok)
        self.assertTrue(state["entities"]["inn_wooden_box"]["is_open"])

    def test_multiple_actions_keep_order_and_use_temporary_state(self):
        engine, _ = self.engine_for({
            "actions": [
                {"tool": "take", "args": {"object_id": "fallen_branch"}},
                {"tool": "equip", "args": {"object_id": "fallen_branch"}},
                {"tool": "inspect", "args": {"target": "fallen_branch"}},
            ]
        })

        _, outcome, state, _ = engine.step("拿起枯木枝，然后装备它，再观察它")

        self.assertTrue(outcome.ok)
        self.assertEqual(
            [item["action"]["tool"] for item in outcome.action_results],
            ["take", "equip", "inspect"],
        )
        self.assertIn("fallen_branch", state["player"]["equipped_items"])
        self.assertEqual(outcome.unresolved_requests[-1]["request"]["kind"], "inspect")

    def test_hard_failure_stops_later_actions_but_keeps_prior_confirmed_result(self):
        engine, _ = self.engine_for({
            "actions": [
                {"tool": "take", "args": {"object_id": "fallen_branch"}},
                {"tool": "open", "args": {"target_id": "fallen_branch"}},
                {"tool": "equip", "args": {"object_id": "fallen_branch"}},
            ]
        })

        _, outcome, state, _ = engine.step("拿起枯木枝，打开它，再装备它")

        self.assertFalse(outcome.ok)
        self.assertEqual([item["action"]["tool"] for item in outcome.action_results], ["take", "open"])
        self.assertEqual(state["entities"]["fallen_branch"]["holder"], "lu_chen")
        self.assertNotIn("fallen_branch", state["player"].get("equipped_items", []))

    def test_remote_object_is_rejected_by_tool_precondition(self):
        engine, resolver = self.engine_for({"actions": []})
        state = engine.get_state()

        outcome = resolver.resolve_actions(
            state,
            ActionBundle("打开远处木箱", [ActionAtom("open", {"target_id": "inn_wooden_box"})]),
        )

        self.assertFalse(outcome.ok)
        self.assertIn("可见或可触及范围", outcome.message)
        self.assertFalse(state["entities"]["inn_wooden_box"]["is_open"])

    def test_malformed_direct_argument_is_a_hard_failure_not_a_crash(self):
        engine, resolver = self.engine_for({"actions": []})

        outcome = resolver.resolve_actions(
            engine.get_state(),
            ActionBundle("拿起东西", [ActionAtom("take", {"object_id": []})]),
        )

        self.assertFalse(outcome.ok)
        self.assertEqual(len(outcome.action_results), 1)

    def test_strike_stays_an_unresolved_attempt(self):
        engine, _ = self.engine_for({
            "actions": [{"tool": "strike", "args": {"target": "tree"}}]
        })

        _, outcome, state, _ = engine.step("打那棵树")

        self.assertTrue(outcome.ok)
        self.assertEqual(outcome.unresolved_requests[0]["request"]["kind"], "strike")
        self.assertEqual(state["player"]["status"], {"injured": False})

    def test_scene_inspect_keeps_skill_observations(self):
        engine, _ = self.engine_for({"actions": [{"tool": "inspect", "args": {}}]})

        _, outcome, _, _ = engine.step("观察四周")

        self.assertTrue(outcome.ok)
        self.assertIn("兽蹄印", outcome.message)
        self.assertEqual(outcome.skill_checks[0]["skill_id"], "tracking")

    def test_extraordinary_attempt_remains_on_legacy_rejection_path(self):
        engine, _ = self.engine_for({"actions": [{"tool": "move", "args": {"destination_id": "forest"}}]})

        intent, outcome, state, _ = engine.step("使用轻功跳上屋顶")

        self.assertFalse(outcome.ok)
        self.assertTrue(intent.extraordinary)
        self.assertEqual(state["turn"], 1)
        self.assertEqual(state["player"]["location"], "forest")
        self.assertIsNone(state["history"][-1]["action_bundle"])


if __name__ == "__main__":
    unittest.main()
