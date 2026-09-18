import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from novel_world.agents.character import CharacterAgent
from novel_world.agents.intent import IntentAgent
from novel_world.agents.narrator import Narrator
from novel_world.assets.loader import AssetLoader
from novel_world.characters.factory import CharacterFactory, STAT_KEYS
from novel_world.characters.skills import CharacterSkillSystem
from novel_world.engine import GameEngine
from novel_world.infrastructure.llm import MockProvider
from novel_world.infrastructure.storage import JsonStore
from novel_world.world.constitution import WorldConstitution
from novel_world.world.models import Intent
from novel_world.world.resolver import WorldResolver
from novel_world.world.state_manager import StateManager
from novel_world.world.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "beginner_world"


class CharacterSkillSystemTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ASSETS)
        self.system = CharacterSkillSystem(self.assets.skills())
        self.factory = CharacterFactory(self.assets.characters_bundle())
        self.resolver = WorldResolver(self.assets, ToolRegistry(self.assets), self.system)

    def player(self, character_id, location=None):
        actor = self.factory.from_preset(self.assets.get_character(character_id))
        if location:
            actor["location"] = location
        return actor

    def test_skill_assets_are_valid_and_all_character_levels_are_bounded(self):
        skill_ids = {skill["id"] for skill in self.assets.skills()}
        self.assertEqual(len(skill_ids), len(self.assets.skills()))
        for skill in self.assets.skills():
            self.assertTrue(set(skill["related_stats"]).issubset(STAT_KEYS))
        for character in self.assets.characters():
            for skill_id, level in character["skills"].items():
                self.assertIn(skill_id, skill_ids)
                self.assertIsInstance(level, int)
                self.assertTrue(0 <= level <= 5)

    def test_evaluation_is_pure_and_higher_skill_is_stronger(self):
        actor = self.player("lu_chen")
        before = deepcopy(actor)
        skilled = self.system.evaluate(actor, "tracking", 2.5)
        self.assertEqual(actor, before)
        novice_actor = deepcopy(actor)
        novice_actor["skills"]["tracking"] = 1
        novice = self.system.evaluate(novice_actor, "tracking", 2.5)
        self.assertGreater(skilled.effective_score, novice.effective_score)

    def test_trained_only_skill_is_blocked_at_level_zero(self):
        actor = {"id": "untrained", "skills": {}, "stats": {key: 5 for key in STAT_KEYS}}
        evaluation = self.system.evaluate(actor, "literacy", 1)
        self.assertEqual(evaluation.grade, "blocked")
        self.assertEqual(evaluation.effective_score, 0.0)

    def test_specialists_outperform_untrained_actors(self):
        untrained = {"id": "untrained", "skills": {}, "stats": {key: 4 for key in STAT_KEYS}}
        self.assertGreater(
            self.system.evaluate(self.player("lu_chen"), "tracking", 2.5).effective_score,
            self.system.evaluate(untrained, "tracking", 2.5).effective_score,
        )
        self.assertGreater(
            self.system.evaluate(self.player("shen_qinghe"), "herbalism", 2.8).effective_score,
            self.system.evaluate(untrained, "herbalism", 2.8).effective_score,
        )

    def test_inspect_reveals_authored_tracking_and_herbalism_observations(self):
        forest = self.resolver.resolve(
            {"player": self.player("lu_chen", "forest"), "actors": {}},
            Intent(kind="inspect", raw_text="观察"),
        )
        self.assertIn("兽蹄印", forest.message)
        self.assertEqual(forest.skill_checks[0]["skill_id"], "tracking")
        herbs = self.resolver.resolve(
            {"player": self.player("shen_qinghe", "herbal_shop"), "actors": {}},
            Intent(kind="inspect", raw_text="观察"),
        )
        self.assertIn("金银花", herbs.message)
        self.assertEqual(herbs.skill_checks[0]["skill_id"], "herbalism")

    def test_npc_runtime_skills_and_history_include_skill_checks(self):
        constitution = WorldConstitution(ROOT / "skills" / "world_core")
        llm = MockProvider()
        with TemporaryDirectory() as temp_dir:
            engine = GameEngine(
                constitution=constitution,
                assets=self.assets,
                intent_agent=IntentAgent(self.assets, llm, constitution),
                character_agent=CharacterAgent(self.assets, llm, constitution),
                resolver=self.resolver,
                state_manager=StateManager(),
                narrator=Narrator(self.assets, llm, constitution),
                store=JsonStore(Path(temp_dir) / "save.json"),
            )
            initial = engine.create_state(self.player("lu_chen", "forest"))
            self.assertEqual(initial["actors"]["shen_qinghe"]["skills"]["herbalism"], 4)
            self.assertEqual(initial["actors"]["shen_qinghe"]["stats"]["intellect"], 7)
            _, outcome, state, _ = engine.step("看看四周")
        self.assertTrue(outcome.skill_checks)
        self.assertEqual(state["history"][-1]["outcome"]["skill_checks"], outcome.skill_checks)


if __name__ == "__main__":
    unittest.main()
