from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Protocol


class LLMProvider(Protocol):
    provider_name: str

    def text(self, *, system: str, user: str, temperature: float = 0.5) -> str:
        ...

    def json(self, *, system: str, user: str, temperature: float = 0.2) -> dict[str, Any]:
        ...


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError(f"LLM 没有返回可解析 JSON：{text[:300]}")

    return json.loads(match.group(0))


@dataclass
class OpenAICompatibleProvider:
    """
    最小 OpenAI-compatible /chat/completions Provider。

    不把任何具体供应商写死在核心代码里。
    """

    base_url: str
    api_key: str
    model: str
    timeout: int = 90
    provider_name: str = "openai_compatible"

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        base_url = os.getenv("NOVEL_WORLD_BASE_URL", "").strip()
        api_key = os.getenv("NOVEL_WORLD_API_KEY", "").strip()
        model = os.getenv("NOVEL_WORLD_MODEL", "").strip()

        if not base_url:
            raise RuntimeError("缺少 NOVEL_WORLD_BASE_URL")
        if not api_key:
            raise RuntimeError("缺少 NOVEL_WORLD_API_KEY")
        if not model:
            raise RuntimeError("缺少 NOVEL_WORLD_MODEL")

        return cls(
            base_url=base_url,
            api_key=api_key,
            model=model,
        )

    def _request(self, *, system: str, user: str, temperature: float) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LLM API HTTP {e.code}: {detail[:1000]}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"无法连接 LLM API：{e}") from e

        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(
                "API 返回格式不是预期的 OpenAI-compatible chat/completions。"
            ) from e

    def text(self, *, system: str, user: str, temperature: float = 0.5) -> str:
        return self._request(system=system, user=user, temperature=temperature).strip()

    def json(self, *, system: str, user: str, temperature: float = 0.2) -> dict[str, Any]:
        content = self._request(
            system=system + "\n只输出一个 JSON 对象，不要使用 Markdown 代码块。",
            user=user,
            temperature=temperature,
        )
        return _extract_json(content)


class MockProvider:
    provider_name = "mock"

    def text(self, *, system: str, user: str, temperature: float = 0.5) -> str:
        return ""

    def json(self, *, system: str, user: str, temperature: float = 0.2) -> dict[str, Any]:
        raise NotImplementedError("MockProvider 由各 Agent 的 fallback 逻辑处理。")
