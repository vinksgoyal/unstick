"""Generate candidate actions for each goal using local Ollama.

Run: ./.venv/bin/python training/generate_candidates.py training/goals.txt \
        --output training/candidates.jsonl --per-goal 12
"""
import argparse
import json
import os
import re
from pathlib import Path

import httpx

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

STATES = [
    {"minutes": 5, "energy": 1, "location": "home", "time": "22:30"},
    {"minutes": 15, "energy": 2, "location": "home", "time": "21:30"},
    {"minutes": 15, "energy": 3, "location": "home", "time": "19:45"},
]

PROMPT = """You generate tiny physical actions for a person who is
overwhelmed by a big creative project. Rules for a GOOD action:
- physical, not mental
- takes 5 minutes or less
- requires no decision from the user
- requires no other person
- does NOT reveal how much work remains, and does NOT require learning a new tool

Return ONLY a JSON object: {{"actions": ["...", "...", "..."]}}
Generate {n} candidate actions for this goal.

Goal: {goal}
State: {state}
"""


def call_ollama(prompt: str) -> list[str]:
    response = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=180,
    )
    if not response.is_success:
        return []
    raw = response.json().get("response", "")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # try to grab the first JSON-looking blob
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    actions = data.get("actions") or data.get("action_strings") or []
    if isinstance(actions, str):
        actions = [actions]
    return [str(a).strip() for a in actions if str(a).strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("goals", type=Path)
    parser.add_argument("--output", type=Path, default=Path("training/candidates.jsonl"))
    parser.add_argument("--per-goal", type=int, default=12)
    args = parser.parse_args()

    goals = [line.strip() for line in args.goals.read_text().splitlines() if line.strip()]
    seen: set[tuple[str, str]] = set()
    total = 0
    with args.output.open("w") as target:
        for goal in goals:
            for state in STATES:
                prompt = PROMPT.format(n=args.per_goal, goal=goal, state=json.dumps(state))
                for action in call_ollama(prompt):
                    key = (goal, action)
                    if key in seen:
                        continue
                    seen.add(key)
                    target.write(json.dumps({"goal": goal, "state": state, "action": action}) + "\n")
                    total += 1
            print(f"done: {goal} ({total} rows so far)")
    print(f"wrote {total} candidates to {args.output}")


if __name__ == "__main__":
    main()
