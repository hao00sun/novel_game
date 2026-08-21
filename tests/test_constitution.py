import unittest
from pathlib import Path

from novel_world.world.constitution import WorldConstitution
from novel_world.assets.loader import AssetLoader
from novel_world.world.models import Outcome
from novel_world.world.state_manager import StateManager


ROOT = Path(__file__).resolve().parents[1]


class ConstitutionTests(unittest.TestCase):
    def setUp(self):
        self.constitution = WorldConstitution(
            ROOT / "skills" / "world_core"
        )
        self.assets = AssetLoader(
            ROOT / "assets" / "beginner_world"
        )

    def test_constitution_is_l0_immutable(self):
        manifest = self.constitution.manifest
        self.assertEqual(manifest["layer"], "L0")
        self.assertEqual(manifest["mutability"], "immutable")

    def test_world_requires_same_constitution(self):
        self.constitution.assert_world_compatible(
            self.assets.world()
        )

    def test_runtime_cannot_modify_constitution(self):
        state = {
            "_meta": {
                "constitution_skill_id": "world_core_constitution"
            },
            "player": {"location": "east_gate"},
            "events": [],
            "turn": 0,
        }

        outcome = Outcome(
            ok=True,
            message="malicious test",
            state_changes=[
                {
                    "path": "_meta.constitution_skill_id",
                    "value": "hacked"
                }
            ]
        )

        with self.assertRaises(PermissionError):
            StateManager().apply(state, outcome)


if __name__ == "__main__":
    unittest.main()
