import os
from dataclasses import dataclass


@dataclass
class TinkerResult:
    scope_safe: bool
    fail_type: str | None = None
    rewrite: str | None = None


class TinkerAdapter:
    """Adapter boundary for the Tinker SDK; verify SDK training/sampling calls before enabling."""

    def __init__(self) -> None:
        self.model_id = os.getenv("TINKER_MODEL_ID")

    def classify(self, goal: str, state: dict, action: str) -> TinkerResult:
        if not self.model_id:
            return TinkerResult(scope_safe=True)
        # TODO: verify against official Tinker SDK docs before implementing sampling.
        raise RuntimeError("Tinker model adapter is configured but not implemented; verify the official SDK")
