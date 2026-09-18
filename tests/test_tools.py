import unittest
from copy import deepcopy
from pathlib import Path

from novel_world.assets.loader import AssetLoader
from novel_world.characters.factory import CharacterFactory
from novel_world.world.models import Outcome
from novel_world.world.state_manager import StateManager
from novel_world.world.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "beginner_world"


class ToolRegistryTests(unittest.TestCase):
    def setUp(self):
        self.assets = AssetLoader(ASSETS)
        self.tools = ToolRegistry(self.assets)
        player = CharacterFactory(self.assets.characters_bundle()).from_preset(
            self.assets.get_character("lu_chen")
        )
        player.update({"held_items": [], "equipped_items": []})
        self.state = {
            "player": player,
            "actors": {"han_ping": {"location": "east_gate", "present": True, "inventory": []}},
            "entities": {item["id"]: deepcopy(item) for item in self.assets.objects()},
            "world_time": {"elapsed_minutes": 0},
            "events": [],
            "turn": 0,
        }
        for entity in self.state["entities"].values():
            entity.setdefault("holder", None)
            entity.setdefault("contained_in", None)
            entity.setdefault("contents", [])

    def commit(self, result):
        outcome = Outcome(
            ok=True,
            message=result["message"],
            state_changes=result["state_changes"],
            events=result["events"],
        )
        self.state = StateManager().apply(self.state, outcome)

    def take_paper(self):
        result = self.tools.take(self.state, "blank_paper")
        self.assertEqual(self.state["entities"]["blank_paper"]["holder"], None)
        self.commit(result)

    def test_perception_and_movement_tools_keep_uncertain_results_as_requests(self):
        self.assertEqual(self.tools.look(self.state, "东门")["perception_requests"][0]["kind"], "look")
        self.assertEqual(self.tools.listen(self.state, "街道")["perception_requests"][0]["kind"], "listen")
        self.assertEqual(self.tools.inspect(self.state, "east_gate_notice")["perception_requests"][0]["kind"], "inspect")
        self.assertEqual(self.tools.search(self.state, "这里")["perception_requests"][0]["kind"], "search")
        self.commit(self.tools.turn(self.state, "北"))
        self.commit(self.tools.change_posture(self.state, "蹲下"))
        self.commit(self.tools.wait(self.state, 3))
        self.assertEqual(self.state["player"]["facing"], "北")
        self.assertEqual(self.state["player"]["posture"], "crouching")
        self.assertEqual(self.state["world_time"]["elapsed_minutes"], 3)

    def test_object_tools_require_commit_and_preserve_container_rules(self):
        self.take_paper()
        self.commit(self.tools.write(self.state, "留给后来者。", "blank_paper"))
        self.assertEqual(self.state["entities"]["blank_paper"]["content"], "留给后来者。")
        self.assertEqual(self.tools.read(self.state, "blank_paper")["perception_requests"][0]["kind"], "read")
        self.commit(self.tools.transfer(self.state, "blank_paper", "han_ping"))
        self.assertIn("blank_paper", self.state["actors"]["han_ping"]["inventory"])
        self.state["player"]["location"] = "inn"
        self.commit(self.tools.open(self.state, "inn_wooden_box"))
        self.commit(self.tools.close(self.state, "inn_wooden_box"))
        self.assertFalse(self.state["entities"]["inn_wooden_box"]["is_open"])

    def test_release_place_and_store_change_only_after_commit(self):
        self.take_paper()
        self.commit(self.tools.release(self.state, "blank_paper"))
        self.assertEqual(self.state["entities"]["blank_paper"]["location"], "east_gate")
        self.commit(self.tools.take(self.state, "blank_paper"))
        self.commit(self.tools.place(self.state, "blank_paper", "ground"))
        self.assertIsNone(self.state["entities"]["blank_paper"]["holder"])
        self.commit(self.tools.take(self.state, "blank_paper"))
        self.state["player"]["location"] = "inn"
        self.commit(self.tools.open(self.state, "inn_wooden_box"))
        self.commit(self.tools.store(self.state, "blank_paper", "inn_wooden_box"))
        self.assertEqual(self.state["entities"]["blank_paper"]["contained_in"], "inn_wooden_box")
        self.assertIn("blank_paper", self.state["entities"]["inn_wooden_box"]["contents"])

    def test_mechanics_defense_and_communication_are_candidate_requests(self):
        self.assertEqual(self.tools.push(self.state, "han_ping", "轻")["action_requests"][0]["kind"], "push")
        self.assertEqual(self.tools.pull(self.state, "han_ping", "轻")["action_requests"][0]["kind"], "pull")
        self.commit(self.tools.grab(self.state, "han_ping"))
        self.assertEqual(self.state["player"]["grabbed_target"], "han_ping")
        self.state["player"]["location"] = "forest"
        self.commit(self.tools.take(self.state, "fallen_branch"))
        self.commit(self.tools.equip(self.state, "fallen_branch"))
        self.assertEqual(self.tools.use(self.state, "fallen_branch")["action_requests"][0]["kind"], "use")
        self.assertEqual(self.tools.throw(self.state, "fallen_branch", "前方")["action_requests"][0]["kind"], "throw")
        self.assertEqual(self.tools.strike(self.state, "树", "fallen_branch")["action_requests"][0]["kind"], "strike")
        self.assertEqual(self.tools.block(self.state, "攻击")["action_requests"][0]["kind"], "block")
        self.assertEqual(self.tools.dodge(self.state, "左")["action_requests"][0]["kind"], "dodge")
        self.state["player"]["location"] = "east_gate"
        self.assertEqual(self.tools.speak(self.state, "你好", "han_ping")["action_requests"][0]["kind"], "speak")
        self.assertEqual(self.tools.gesture(self.state, "点头", "han_ping")["action_requests"][0]["kind"], "gesture")


if __name__ == "__main__":
    unittest.main()
