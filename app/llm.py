import os
from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma2:2b")

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            return response.is_success
        except httpx.HTTPError:
            return False

    def candidates(self, goal: str, state: dict[str, Any]) -> list[str]:
        prompt = (
            "Return exactly three JSON action strings. Each must be a physical action, "
            "take five minutes or less, require no choice or person, and reveal no scope. "
            f"Goal: {goal}\nState: {state}"
        )
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        generated = data.get("response", "")
        if isinstance(generated, list):
            return [str(item) for item in generated]
        return [generated] if generated else []
