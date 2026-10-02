"""Send each candidate to Ollama with a strict classifier prompt.

The point: use a LARGER model (or the same Gemma but with a very clear prompt)
to label the review candidates automatically, so I only need to spot-check.
"""
import json
import os
from pathlib import Path

import httpx

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

PROMPT = """You are labeling training data for a tool that gives tiny physical
actions to an overwhelmed user. Decide if the ACTION helps with the GOAL.

Rules for a GOOD action (scope_safe = true):
- physical, not mental
- takes 5 minutes or less
- requires no decision from the user
- requires no other person
- does NOT reveal how much work exists
- does NOT require learning a new tool
- is clearly related to the goal

If GOOD: return {{"scope_safe": true, "fail_type": null}}
If BAD, pick exactly one fail_type:
  "reveals_scope"       - hints at how much work exists ("plan", "design your site", "outline")
  "needs_new_skill"     - requires learning a tool ("learn Figma", "set up Lightroom")
  "needs_decision"      - asks the user to choose ("pick your best", "decide on")
  "not_physical"        - mental-only ("think about", "reflect on", "imagine")
  "needs_other_person"  - depends on someone else ("ask a friend", "email")
  "off_topic"           - unrelated to the goal (e.g. "pour water" for a portfolio goal)

Return ONLY: {{"scope_safe": bool, "fail_type": str|null}}

Goal: {goal}
Action: {action}
"""


def classify(goal: str, action: str) -> dict:
    prompt = PROMPT.format(goal=goal, action=action)
    response = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=120,
    )
    if not response.is_success:
        return {"scope_safe": False, "fail_type": "off_topic"}
    try:
        data = json.loads(response.json().get("response", "{}"))
    except json.JSONDecodeError:
        return {"scope_safe": False, "fail_type": "off_topic"}
    return data


def main() -> None:
    src = Path("training/needs_review.jsonl")
    dst = Path("training/copilot_labeled.jsonl")
    rows = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    total = len(rows)
    with dst.open("w") as out:
        for i, rec in enumerate(rows, 1):
            verdict = classify(rec["goal"], rec["action"])
            rec["scope_safe"] = bool(verdict.get("scope_safe"))
            rec["fail_type"] = verdict.get("fail_type") if not rec["scope_safe"] else None
            rec["rewrite"] = None
            out.write(json.dumps(rec) + "\n")
            out.flush()
            print(f"[{i}/{total}] {rec['scope_safe']} {rec['fail_type']}: {rec['action'][:60]}")
    print(f"wrote {total} rows to {dst}")


if __name__ == "__main__":
    main()
