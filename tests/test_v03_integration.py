import unittest
from pathlib import Path

from novel_world.asset_loader import AssetLoader
from novel_world.character_factory import CharacterFactory
from novel_world.constitution import WorldConstitution
from novel_world.intent_agent import IntentAgent
from novel_world.character_agent import CharacterAgent
from novel_world.llm import MockProvider
from novel_world.tools import ToolRegistry
from novel_world.resolver import WorldResolver
from novel_world.state_manager import StateManager

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


if __name__ == "__main__":
    unittest.main()
