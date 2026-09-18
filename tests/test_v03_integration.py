import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from novel_world.assets.loader import AssetLoader
from novel_world.characters.factory import CharacterFactory
from novel_world.world.constitution import WorldConstitution
from novel_world.agents.intent import IntentAgent
from novel_world.agents.character import CharacterAgent
from novel_world.agents.narrator import Narrator
from novel_world.engine import GameEngine
from novel_world.infrastructure.llm import MockProvider
from novel_world.infrastructure.storage import JsonStore
from novel_world.world.tools import ToolRegistry
from novel_world.world.resolver import WorldResolver
from novel_world.world.state_manager import StateManager

ROOT = Path(__file__).resolve().parents[1]


class V03IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ROOT / "assets" / "beginner_world")
        self.constitution = WorldConstitution(ROOT / "skills" / "world_core")
        self.llm = MockProvider()

        factory = CharacterFactory(self.assets.characters_bundle())
        player = factory.from_preset(self.assets.get_character("lu_chen"))

        self.state = {
            "player": player,
            "actors": {
                c["id"]: {
                    "location": c["location"],
                    "present": True,
                    "goals": c.get("agent_profile", {}).get("goals", []),
                    "beliefs": c.get("agent_profile", {}).get("beliefs", []),
                    "emotion": c.get("agent_profile", {}).get("emotion", {"state": "平静"}),
                    "relationship_context": [],
                    "memory": [],
                }
                for c in self.assets.characters()
                if c["id"] != "lu_chen"
            },
            "events": [],
            "turn": 0,
        }

    def test_llm_guardrails_exist(self):
        text = self.constitution.llm_guardrails
        self.assertIn("World State", text)
        self.assertIn("结果自由", text)

    def test_compound_move_and_talk(self):
        intent_agent = IntentAgent(self.assets, self.llm, self.constitution)
        character_agent = CharacterAgent(self.assets, self.llm, self.constitution)
        resolver = WorldResolver(self.assets, ToolRegistry(self.assets))

        intent = intent_agent.interpret("去药铺和沈青禾聊聊", self.state)
        self.assertEqual(intent.kind, "talk")
        self.assertEqual(intent.destination, "herbal_shop")
        self.assertEqual(intent.target, "shen_qinghe")

        proposal = character_agent.react("shen_qinghe", self.state, intent)
        outcome = resolver.resolve(self.state, intent, npc_proposal=proposal)
        self.assertTrue(outcome.ok)

        new_state = StateManager().apply(self.state, outcome)
        self.assertEqual(new_state["player"]["location"], "herbal_shop")

    def test_engine_can_commit_forest_movement(self):
        player = CharacterFactory(self.assets.characters_bundle()).from_preset(
            self.assets.get_character("lu_chen")
        )
        with TemporaryDirectory() as temp_dir:
            engine = GameEngine(
                constitution=self.constitution,
                assets=self.assets,
                intent_agent=IntentAgent(self.assets, self.llm, self.constitution),
                character_agent=CharacterAgent(self.assets, self.llm, self.constitution),
                resolver=WorldResolver(self.assets, ToolRegistry(self.assets)),
                state_manager=StateManager(),
                narrator=Narrator(self.assets, self.llm, self.constitution),
                store=JsonStore(Path(temp_dir) / "save.json"),
            )
            initial_state = engine.create_state(player)
            self.assertIn("east_gate_notice", initial_state["entities"])
            self.assertEqual(initial_state["world_time"]["elapsed_minutes"], 0)
            _, outcome, state, _ = engine.step("去山林")

        self.assertTrue(outcome.ok)
        self.assertEqual(state["player"]["location"], "forest")


if __name__ == "__main__":
    unittest.main()
