import json
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
from novel_world.world.models import Outcome
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
        self.payload = None

    def json(self, *, system, user, temperature=0.2):
        self.payload = json.loads(user)
        return self.response


class InitialAssetTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ROOT / "assets" / "beginner_world")
        self.constitution = WorldConstitution(ROOT / "skills" / "world_core")
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def build_engine(self, response=None, player_id="lu_chen", location=None):
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
        provider = StubActionProvider(response or {"actions": []})
        player = CharacterFactory(self.assets.characters_bundle()).from_preset(
            self.assets.get_character(player_id)
        )
        if location:
            player["location"] = location
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
        return engine, tools, provider, engine.create_state(player)

    def test_preset_inventory_uses_owned_entity_ids(self):
        _, _, _, state = self.build_engine()
        player = state["player"]

        self.assertEqual(player["held_items"], [])
        self.assertEqual(player["equipped_items"], [])
        self.assertNotIn("猎刀", player["inventory"])
        self.assertNotIn("短弓", player["inventory"])
        for object_id in player["inventory"]:
            self.assertIn(object_id, state["entities"])
            self.assertEqual(state["entities"][object_id]["holder"], player["id"])
            self.assertIsNone(state["entities"][object_id]["location"])

    def test_scene_and_npc_owned_entities_have_unambiguous_ownership(self):
        _, _, _, state = self.build_engine()

        self.assertEqual(state["entities"]["fallen_branch"]["location"], "forest")
        self.assertIsNone(state["entities"]["fallen_branch"]["holder"])
        for npc in state["actors"].values():
            self.assertEqual(npc["held_items"], [])
            self.assertEqual(npc["equipped_items"], [])
            for object_id in npc["inventory"]:
                self.assertIn(object_id, state["entities"])
                self.assertEqual(state["entities"][object_id]["holder"], npc["id"])
                self.assertIsNone(state["entities"][object_id]["location"])

    def test_custom_character_starts_with_empty_item_collections(self):
        factory = CharacterFactory(self.assets.characters_bundle())
        player = factory.create_custom(
            "无名", "平民", {key: 5 for key in factory.bundle["stat_schema"]}, "east_gate"
        )
        engine, _, _, _ = self.build_engine()
        state = engine.create_state(player)

        self.assertEqual(state["player"]["inventory"], [])
        self.assertEqual(state["player"]["held_items"], [])
        self.assertEqual(state["player"]["equipped_items"], [])

    def test_take_and_release_keep_entity_and_inventory_consistent(self):
        engine, tools, _, state = self.build_engine(location="forest")
        manager = engine.state_manager

        state = manager.apply(state, Outcome(ok=True, **tools.take(state, "fallen_branch")))
        self.assertIn("fallen_branch", state["player"]["inventory"])
        self.assertEqual(state["entities"]["fallen_branch"]["holder"], "lu_chen")
        self.assertIsNone(state["entities"]["fallen_branch"]["location"])

        state = manager.apply(state, Outcome(ok=True, **tools.release(state, "fallen_branch")))
        self.assertNotIn("fallen_branch", state["player"]["inventory"])
        self.assertIsNone(state["entities"]["fallen_branch"]["holder"])
        self.assertEqual(state["entities"]["fallen_branch"]["location"], "forest")

    def test_reference_context_and_inspect_use_hunting_knife_entity_id(self):
        engine, _, provider, state = self.build_engine({
            "actions": [{"tool": "inspect", "args": {"target": "lu_chen_hunting_knife"}}]
        })

        bundle = engine.intent_agent.interpret_actions("检查一下我的猎刀", state)

        knife = next(item for item in provider.payload["reference_context"]["entities"] if item["id"] == "lu_chen_hunting_knife")
        self.assertEqual(knife["name"], "猎刀")
        self.assertEqual(knife["relation"], "inventory")
        self.assertEqual(bundle.actions[0].args["target"], "lu_chen_hunting_knife")

    def test_equip_hunting_knife_runs_full_action_path_by_entity_id(self):
        engine, tools, _, _ = self.build_engine({
            "actions": [{"tool": "equip", "args": {"object_id": "lu_chen_hunting_knife"}}]
        })

        with self.assertRaises(ValueError):
            tools.equip(engine.get_state(), "猎刀")
        intent, outcome, state, _ = engine.step("装备猎刀")

        self.assertEqual(intent.kind, "action_bundle")
        self.assertTrue(outcome.ok)
        self.assertIn("lu_chen_hunting_knife", state["player"]["equipped_items"])
        self.assertIn("猎刀", outcome.message)
        self.assertNotIn("lu_chen_hunting_knife", outcome.message)

    def test_old_display_name_inventory_save_requires_reset(self):
        engine, _, _, state = self.build_engine()
        state["player"]["inventory"] = ["猎刀"]
        engine.store.save(state)

        with self.assertRaisesRegex(ValueError, "/reset"):
            engine.get_state()


if __name__ == "__main__":
    unittest.main()
