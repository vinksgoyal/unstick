import hashlib
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException

from .constraints import check
from .llm import OllamaClient
from .memory import BehaviourMemory
from .models import Action, CompleteRequest, UnstickRequest, UnstickResponse
from .storage import LocalStorage
from .tinker_client import TinkerAdapter

logger = logging.getLogger(__name__)
router = APIRouter()
ollama = OllamaClient()
tinker = TinkerAdapter()
memory = BehaviourMemory()
storage = LocalStorage(os.getenv("DATABASE_PATH", "unstick.db"))


def _fallback_actions() -> list[str]:
    return ["Open a blank note and type the title of one finished piece.", "Save one existing file with a shorter name.", "Move one finished piece into a folder called maybe."]


@router.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "ollama_available": ollama.is_available()}


@router.post("/unstick", response_model=UnstickResponse)
def unstick(request: UnstickRequest) -> UnstickResponse:
    state = request.model_dump(exclude={"goal"})
    try:
        behavioural_context = memory.context(state)
        candidates = ollama.candidates(request.goal, {**state, "behaviour": behavioural_context}) if ollama.is_available() else _fallback_actions()
    except Exception as exc:
        logger.warning("ollama call failed, using fallback: %s", exc)
        candidates = _fallback_actions()
    passing: list[tuple[str, dict]] = []
    for candidate in candidates:
        result = tinker.classify(request.goal, state, candidate)
        action = result.rewrite if not result.scope_safe and result.rewrite else candidate
        verdict = check(action, state)
        if verdict["passes"]:
            passing.append((action, verdict))
    for fallback in _fallback_actions():
        verdict = check(fallback, state)
        if verdict["passes"] and len(passing) < 3:
            passing.append((fallback, verdict))
    unique = list(dict((text, verdict) for text, verdict in passing).items())[:3]
    if len(unique) < 3:
        raise HTTPException(status_code=503, detail="Could not produce three safe actions")
    goal_id = hashlib.sha256(request.goal.encode()).hexdigest()[:16]
    return UnstickResponse(
        start_here=Action(text=unique[0][0], constraints=unique[0][1]),
        if_you_have_15=Action(text=unique[1][0], constraints=unique[1][1], estimated_minutes=5),
        not_today={"message": "The rest of the plan exists. You don't need to see it."},
        model_used="base-gemma2" if ollama.is_available() else "fallback",
        privacy_note=f"content stayed local (goal {goal_id})",
    )


@router.post("/complete")
def complete(request: CompleteRequest) -> dict[str, str]:
    storage.record_completion(request.goal_id, request.action_id, request.completed)
    memory.record({
        "goal_id": request.goal_id, "action_type": request.action_id,
        "completed": request.completed, "energy": 0, "minutes": 0, "time_bucket": "unknown",
    })
    return {"status": "recorded"}
