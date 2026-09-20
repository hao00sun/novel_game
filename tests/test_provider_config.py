import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from novel_world.infrastructure.config import save_provider_config


class ProviderConfigTests(unittest.TestCase):
    def test_api_configuration_preserves_unrelated_env_entries(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("UNRELATED=value\nNOVEL_WORLD_PROVIDER=mock\n", encoding="utf-8")
            save_provider_config(
                env_path,
                "api",
                base_url="https://example.test/v1",
                api_key="secret-key",
                model="test-model",
            )
            saved = env_path.read_text(encoding="utf-8")

        self.assertIn("UNRELATED=value", saved)
        self.assertIn("NOVEL_WORLD_PROVIDER=api", saved)
        self.assertIn("NOVEL_WORLD_BASE_URL=https://example.test/v1", saved)
        self.assertIn("NOVEL_WORLD_MODEL=test-model", saved)

    def test_api_configuration_requires_all_connection_values(self):
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                save_provider_config(Path(temp_dir) / ".env", "api", model="missing-values")


if __name__ == "__main__":
    unittest.main()
