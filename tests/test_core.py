import tempfile
import unittest
from pathlib import Path

from novel_world.assets.loader import AssetLoader
from novel_world.characters.factory import CharacterFactory
from novel_world.agents.intent import IntentAgent
from novel_world.infrastructure.llm import MockProvider
from novel_world.world.tools import ToolRegistry
from novel_world.world.resolver import WorldResolver
from novel_world.world.state_manager import StateManager
from novel_world.world.models import Intent


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "beginner_world"


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ASSETS)
        self.factory = CharacterFactory(self.assets.characters_bundle())
        self.tools = ToolRegistry(self.assets)
        self.resolver = WorldResolver(self.assets, self.tools)

    def test_official_is_not_selectable(self):
        official = self.assets.get_character("magistrate_xu")
        with self.assertRaises(ValueError):
            self.factory.from_preset(official)

    def test_custom_budget(self):
        with self.assertRaises(ValueError):
            self.factory.create_custom(
                "测试",
                "平民",
                {
                    "physique": 8,
                    "agility": 8,
                    "intellect": 8,
                    "perception": 8,
                    "social": 1,
                    "will": 1,
                },
                "east_gate",
            )

    def test_extraordinary_rejected(self):
        player = self.factory.from_preset(
            self.assets.get_character("lu_chen")
        )
        state = {
            "player": player,
            "events": [],
            "turn": 0,
        }

        intent = IntentAgent(self.assets, MockProvider()).interpret(
            "使用轻功跳上屋顶", state
        )
        outcome = self.resolver.resolve(state, intent)

        self.assertFalse(outcome.ok)
        self.assertIn("超凡力量", outcome.message)

    def test_move_is_committed_only_by_state_manager(self):
        player = self.factory.from_preset(
            self.assets.get_character("lu_chen")
        )
        state = {
            "player": player,
            "events": [],
            "turn": 0,
        }

        intent = IntentAgent(self.assets, MockProvider()).interpret("去药铺", state)
        outcome = self.resolver.resolve(state, intent)

        self.assertEqual(state["player"]["location"], "east_gate")
        new_state = StateManager().apply(state, outcome)
        self.assertEqual(new_state["player"]["location"], "herbal_shop")

    def test_forest_is_the_only_open_outside_location(self):
        player = self.factory.from_preset(self.assets.get_character("lu_chen"))
        state = {"player": player, "events": [], "turn": 0}

        intent = IntentAgent(self.assets, MockProvider()).interpret("去山林", state)
        outcome = self.resolver.resolve(state, intent)

        self.assertTrue(outcome.ok)
        self.assertEqual(StateManager().apply(state, outcome)["player"]["location"], "forest")
        self.assertTrue(self.assets.is_location_reachable("east_gate", "forest"))

        rejected = self.resolver.resolve(
            state,
            Intent(kind="move", raw_text="去村庄", destination="village"),
        )
        self.assertFalse(rejected.ok)
        self.assertIn("仅开放山林", rejected.message)


if __name__ == "__main__":
    unittest.main()
