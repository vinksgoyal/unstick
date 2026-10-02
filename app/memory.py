import os
from typing import Any


class BehaviourMemory:
    """Backboard adapter that accepts behavioural signals only, never content."""

    def __init__(self) -> None:
        self.api_key = os.getenv("BACKBOARD_API_KEY")
        self.memory_id = os.getenv("BACKBOARD_MEMORY_ID")

    def context(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        # TODO: verify current Backboard SDK/API method and endpoint in official docs.
        raise RuntimeError("Backboard adapter requires official API verification")

    def record(self, signal: dict[str, Any]) -> None:
        allowed = {"goal_id", "energy", "minutes", "time_bucket", "action_type", "completed"}
        if set(signal) - allowed:
            raise ValueError("Only abstract behavioural signals may be sent to Backboard")
        if not self.api_key:
            return
        raise RuntimeError("Backboard adapter requires official API verification")
