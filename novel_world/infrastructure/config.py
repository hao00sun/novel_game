from __future__ import annotations

import os
from getpass import getpass
from pathlib import Path


PROVIDER_KEYS = {
    "NOVEL_WORLD_PROVIDER",
    "NOVEL_WORLD_BASE_URL",
    "NOVEL_WORLD_API_KEY",
    "NOVEL_WORLD_MODEL",
}


def load_env_file(path: str | Path) -> None:
    """
    Minimal .env reader. Existing environment variables always win.
    """
    path = Path(path)
    if not path.exists():
        return

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def save_provider_config(
    path: str | Path,
    provider: str,
    *,
    base_url: str = "",
    api_key: str = "",
    model: str = "",
) -> None:
    """Persist only Novel World provider settings without touching other .env keys."""
    if provider not in {"mock", "api"}:
        raise ValueError("provider must be 'mock' or 'api'.")
    if provider == "api" and not all([base_url.strip(), api_key.strip(), model.strip()]):
        raise ValueError("API 模式需要 Base URL、API Key 和模型名。")

    path = Path(path)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    preserved = [
        line for line in existing
        if line.split("=", 1)[0].strip() not in PROVIDER_KEYS
    ]
    settings = [f"NOVEL_WORLD_PROVIDER={provider}"]
    if provider == "api":
        settings.extend([
            f"NOVEL_WORLD_BASE_URL={base_url.strip()}",
            f"NOVEL_WORLD_API_KEY={api_key.strip()}",
            f"NOVEL_WORLD_MODEL={model.strip()}",
        ])
    path.write_text("\n".join([*preserved, *settings, ""]), encoding="utf-8")


def configure_provider(path: str | Path) -> None:
    """Run a terminal-only provider setup wizard; API Key input is hidden."""
    print("Novel World LLM 配置")
    print("  1. mock（无需 API，使用确定性回退）")
    print("  2. api（OpenAI-compatible /chat/completions）")

    while True:
        choice = input("选择 [1/2] > ").strip()
        if choice in {"1", "mock"}:
            save_provider_config(path, "mock")
            print("已保存 mock 配置。")
            return
        if choice in {"2", "api", "openai_compatible"}:
            base_url = input("Base URL（例：https://api.openai.com/v1） > ").strip()
            api_key = getpass("API Key（输入不会显示） > ").strip()
            model = input("模型名 > ").strip()
            try:
                save_provider_config(
                    path,
                    "api",
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                )
            except ValueError as error:
                print(f"配置未保存：{error}")
                continue
            print("已保存 API 配置。")
            return
        print("请输入 1 或 2。")
