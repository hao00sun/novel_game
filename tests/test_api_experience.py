import unittest
from pathlib import Path

from novel_world.asset_loader import AssetLoader
from novel_world.character_factory import CharacterFactory
from novel_world.llm import MockProvider
from novel_world.intent_agent import IntentAgent
from novel_world.character_agent import CharacterAgent
from novel_world.tools import ToolRegistry
from novel_world.resolver import WorldResolver
from novel_world.state_manager import StateManager


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "beginner_world"


class APIExperienceTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ASSETS)
        self.llm = MockProvider()
        self.intent = IntentAgent(self.assets, self.llm)
        self.character = CharacterAgent(self.assets, self.llm)
        self.tools = ToolRegistry(self.assets)
        self.resolver = WorldResolver(self.assets, self.tools)

        factory = CharacterFactory(self.assets.characters_bundle())
        self.player = factory.from_preset(
            self.assets.get_character("lu_chen")
        )

        self.state = {
            "player": self.player,
            "actors": {
                c["id"]: {
                    "location": c["location"],
                    "present": True,
                    "goals": c.get("agent_profile", {}).get("goals", []),
                    "beliefs": c.get("agent_profile", {}).get("beliefs", []),
                    "emotion": c.get("agent_profile", {}).get(
                        "emotion", {"state": "平静"}
                    ),
                    "relationship_context": [],
                    "memory": [],
                }
                for c in self.assets.characters()
                if c["id"] != "lu_chen"
            },
            "events": [],
            "turn": 0,
        }

    def test_character_asset_has_agent_profile(self):
        shen = self.assets.get_character("shen_qinghe")
        self.assertIn("beliefs", shen["agent_profile"])
        self.assertIn("goals", shen["agent_profile"])

    def test_talk_produces_character_proposal(self):
        self.state["player"]["location"] = "herbal_shop"
        intent = self.intent.interpret("和沈青禾说话", self.state)
        proposal = self.character.react(
            "shen_qinghe", self.state, intent
        )
        outcome = self.resolver.resolve(
            self.state, intent, npc_proposal=proposal
        )

        self.assertTrue(outcome.ok)
        self.assertIsNotNone(outcome.npc_proposal)

    def test_extraordinary_still_rejected_after_api_layer(self):
        intent = self.intent.interpret("我用轻功跳上屋顶", self.state)
        outcome = self.resolver.resolve(self.state, intent)
        self.assertFalse(outcome.ok)

    def test_npc_not_same_as_world_state_commit(self):
        self.state["player"]["location"] = "herbal_shop"
        intent = self.intent.interpret("和沈青禾说话", self.state)
        proposal = self.character.react(
            "shen_qinghe", self.state, intent
        )
        outcome = self.resolver.resolve(
            self.state, intent, npc_proposal=proposal
        )

        # Proposal exists before commit.
        old_emotion = self.state["actors"]["shen_qinghe"]["emotion"]["state"]
        new_state = StateManager().apply(self.state, outcome)

        # Original state remains unchanged.
        self.assertEqual(
            self.state["actors"]["shen_qinghe"]["emotion"]["state"],
            old_emotion
        )
        self.assertEqual(new_state["turn"], 1)


if __name__ == "__main__":
    unittest.main()
