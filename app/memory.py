"""Backboard behavioural memory adapter.

Only abstract behavioural signals cross the wire. Never content.
Signals: {goal_id, energy, minutes, time_bucket, action_type, completed}
"""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://app.backboard.io/api"


class BehaviourMemory:
    def __init__(self) -> None:
        self.api_key = os.getenv("BACKBOARD_API_KEY")
        self.assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key or "", "Content-Type": "application/json"}

    def context(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.api_key or not self.assistant_id:
            return []
        try:
            response = httpx.post(
                f"{BASE_URL}/assistants/{self.assistant_id}/memories/search",
                headers=self._headers(),
                json={"query": "what kinds of actions does this user complete", "limit": 5},
                timeout=10,
            )
            if not response.is_success:
                logger.warning("Backboard search failed: %s", response.status_code)
                return []
            return response.json().get("memories", [])
        except Exception as exc:
            logger.warning("Backboard search error: %s", exc)
            return []

    def record(self, signal: dict[str, Any]) -> None:
        allowed = {"goal_id", "energy", "minutes", "time_bucket", "action_type", "completed"}
        extra = set(signal) - allowed
        if extra:
            raise ValueError(f"Only behavioural signals allowed, got: {extra}")

        if not self.api_key or not self.assistant_id:
            return

        text = (
            f"User has {signal.get('minutes', 0)} minutes and energy "
            f"{signal.get('energy', 0)} at {signal.get('time_bucket', 'unknown')}. "
            f"Action type: {signal.get('action_type', 'unknown')}. "
            f"Completed: {signal.get('completed', False)}."
        )
        try:
            response = httpx.post(
                f"{BASE_URL}/assistants/{self.assistant_id}/memories",
                headers=self._headers(),
                json={"content": text, "metadata": {"source": "unstick", "confidence": "high"}},
                timeout=10,
            )
            if not response.is_success:
                logger.warning("Backboard save failed: %s", response.status_code)
        except Exception as exc:
            logger.warning("Backboard save error: %s", exc)
