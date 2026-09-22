import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from novel_world.agents.character import CharacterAgent
from novel_world.agents.intent import IntentAgent
from novel_world.agents.narrator import Narrator
from novel_world.agents.prompts import NARRATOR_SYSTEM
from novel_world.assets.loader import AssetLoader
from novel_world.characters.factory import CharacterFactory
from novel_world.characters.skills import CharacterSkillSystem
from novel_world.engine import GameEngine
from novel_world.infrastructure.llm import MockProvider
from novel_world.infrastructure.storage import JsonStore
from novel_world.world.action_validator import ActionValidator
from novel_world.world.constitution import WorldConstitution
from novel_world.world.models import Outcome
from novel_world.world.resolver import WorldResolver
from novel_world.world.state_manager import StateManager
from novel_world.world.tool_dispatcher import ToolDispatcher
from novel_world.world.tool_schema import ToolSchema
from novel_world.world.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]
KNIFE_ID = "lu_chen_hunting_knife"


class QueueProvider:
    provider_name = "stub"

    def __init__(self, responses):
        self.responses = list(responses)

    def json(self, *, system, user, temperature=0.2):
        if not self.responses:
            raise AssertionError("Unexpected LLM action parse")
        return self.responses.pop(0)


class PerceptionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ROOT / "assets" / "beginner_world")
        self.constitution = WorldConstitution(ROOT / "skills" / "world_core")
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def engine_for(self, responses):
        tools = ToolRegistry(self.assets)
        schema = ToolSchema.from_registry(tools)
        validator = ActionValidator(schema)
        state_manager = StateManager()
        provider = QueueProvider(responses)
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
        player["location"] = "forest"
        engine = GameEngine(
            constitution=self.constitution,
            assets=self.assets,
            intent_agent=IntentAgent(
                self.assets,
                provider,
                self.constitution,
                action_schema=schema,
                action_validator=validator,
            ),
            character_agent=CharacterAgent(self.assets, MockProvider(), self.constitution),
            resolver=resolver,
            state_manager=state_manager,
            narrator=Narrator(self.assets, MockProvider(), self.constitution),
            store=JsonStore(Path(self.temp_dir.name) / "save.json"),
        )
        engine.create_state(player)
        return engine

    @staticmethod
    def inspect_action(target=None):
        args = {} if target is None else {"target": target}
        return {"actions": [{"tool": "inspect", "args": args}]}

    def test_entity_inspect_sets_focus_without_scene_tracking(self):
        engine = self.engine_for([self.inspect_action(KNIFE_ID)])

        _, outcome, state, _ = engine.step("检查一下猎刀")

        self.assertTrue(outcome.ok)
        self.assertNotIn("兽蹄印", outcome.message)
        self.assertEqual(outcome.skill_checks, [])
        self.assertEqual(state["interaction"]["last_focus_entity_id"], KNIFE_ID)

    def test_scene_inspect_keeps_tracking_and_clears_focus(self):
        engine = self.engine_for([self.inspect_action()])
        state = engine.get_state()
        state["interaction"]["last_focus_entity_id"] = KNIFE_ID
        engine.store.save(state)

        _, outcome, state, _ = engine.step("观察一下周围")

        self.assertIn("兽蹄印", outcome.message)
        self.assertEqual(outcome.skill_checks[0]["skill_id"], "tracking")
        self.assertIsNone(state["interaction"]["last_focus_entity_id"])

    def test_focus_followup_reuses_last_reference_without_llm_guessing(self):
        engine = self.engine_for([self.inspect_action(KNIFE_ID)])
        engine.step("检查一下猎刀")

        _, outcome, state, _ = engine.step("仔细看看")

        action = state["history"][-1]["action_bundle"]["actions"][0]
        self.assertEqual(action["tool"], "inspect")
        self.assertEqual(action["args"]["target"], KNIFE_ID)
        self.assertNotIn("兽蹄印", outcome.message)
        context, _ = engine.intent_agent._build_action_reference_context(state)
        self.assertEqual(context["recent_focus"]["id"], KNIFE_ID)

    def test_explicit_scene_inspection_overrides_focus(self):
        engine = self.engine_for([self.inspect_action(KNIFE_ID), self.inspect_action()])
        engine.step("检查一下猎刀")

        _, outcome, state, _ = engine.step("观察一下周围")

        action = state["history"][-1]["action_bundle"]["actions"][0]
        self.assertEqual(action["args"], {})
        self.assertIn("兽蹄印", outcome.message)
        self.assertIsNone(state["interaction"]["last_focus_entity_id"])

    def test_unreferenceable_focus_is_not_reused(self):
        engine = self.engine_for([])
        state = engine.get_state()
        state["interaction"]["last_focus_entity_id"] = KNIFE_ID
        state["player"]["inventory"].remove(KNIFE_ID)
        state["entities"][KNIFE_ID]["holder"] = None
        state["entities"][KNIFE_ID]["location"] = "inn"
        engine.store.save(state)

        intent, outcome, state, _ = engine.step("仔细看看")

        self.assertEqual(intent.kind, "freeform")
        self.assertIsNone(state["history"][-1]["action_bundle"])
        self.assertNotIn("兽蹄印", outcome.message)

    def test_inventory_overview_is_read_only_and_never_scene_tracking(self):
        engine = self.engine_for([])

        intent, outcome, state, _ = engine.step("检查一下自身装备")

        self.assertEqual(intent.kind, "inventory_overview")
        self.assertIn("猎刀", outcome.message)
        self.assertNotIn(KNIFE_ID, outcome.message)
        self.assertNotIn("兽蹄印", outcome.message)
        self.assertEqual(outcome.skill_checks, [])
        self.assertIsNone(state["interaction"]["last_focus_entity_id"])

    def test_targeted_inspect_requires_a_currently_referenceable_entity(self):
        engine = self.engine_for([])

        outcome = engine.resolver.resolve_actions(
            engine.get_state(),
            engine.intent_agent._validated_action_bundle(
                "检查远处木箱",
                self.inspect_action("inn_wooden_box"),
                {"inn_wooden_box"},
            ),
        )

        self.assertFalse(outcome.ok)
        self.assertIn("可见或可触及范围", outcome.message)

    def test_narrator_prompt_forbids_unconfirmed_physical_placement(self):
        self.assertIn("已确认事实的渲染器", NARRATOR_SYSTEM)
        self.assertIn("腰间、背上、行囊、左右手、皮鞘", NARRATOR_SYSTEM)
        self.assertIn("未裁决的 perception/action request", NARRATOR_SYSTEM)

        narration = Narrator(self.assets, MockProvider()).render(
            old_state={},
            intent=type("Intent", (), {"to_dict": lambda self: {}})(),
            outcome=Outcome(ok=True, message="你装备了猎刀。"),
            new_state={"player": {"location": "forest"}},
        )
        self.assertEqual(narration, "你装备了猎刀。")


if __name__ == "__main__":
    unittest.main()
