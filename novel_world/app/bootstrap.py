from __future__ import annotations

import os
from pathlib import Path

from ..agents.character import CharacterAgent
from ..agents.intent import IntentAgent
from ..agents.narrator import Narrator
from ..assets.loader import AssetLoader
from ..engine import GameEngine
from ..infrastructure.config import load_env_file
from ..infrastructure.llm import MockProvider, OpenAICompatibleProvider
from ..infrastructure.storage import JsonStore
from ..world.constitution import WorldConstitution
from ..world.resolver import WorldResolver
from ..world.state_manager import StateManager
from ..world.tools import ToolRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION_DIR = PROJECT_ROOT / "skills" / "world_core"
ASSET_DIR = PROJECT_ROOT / "assets" / "beginner_world"
SAVE_PATH = PROJECT_ROOT / ".runtime" / "save.json"
ENV_PATH = PROJECT_ROOT / ".env"


def build_llm():
    """Build the configured LLM provider without leaking provider details into domain code."""
    load_env_file(ENV_PATH)
    provider = os.getenv("NOVEL_WORLD_PROVIDER", "mock").lower().strip()

    if provider in {"api", "openai_compatible"}:
        return OpenAICompatibleProvider.from_env()

    return MockProvider()


def build_engine():
    """Compose the application from world, agent, asset and infrastructure modules."""
    constitution = WorldConstitution(CONSTITUTION_DIR)
    assets = AssetLoader(ASSET_DIR)
    llm = build_llm()
    tools = ToolRegistry(assets)

    engine = GameEngine(
        constitution=constitution,
        assets=assets,
        intent_agent=IntentAgent(assets, llm, constitution),
        character_agent=CharacterAgent(assets, llm, constitution),
        resolver=WorldResolver(assets, tools),
        state_manager=StateManager(),
        narrator=Narrator(assets, llm, constitution),
        store=JsonStore(SAVE_PATH),
    )

    return constitution, assets, llm, engine
