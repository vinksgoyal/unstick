import re

SCOPE_BLOCKLIST = (
    "build", "design", "plan", "learn", "research", "decide", "curate",
    "choose", "sketch", "outline", "roadmap", "tutorial", "gallery",
)
ENCOURAGED = (
    "open", "save", "copy", "paste", "move", "rename", "text", "photograph",
    "print", "delete", "archive", "screenshot", "label",
)
TOOL_NAMES = ("figma", "webflow", "lightroom", "photoshop", "illustrator", "ableton")
DECISION_PATTERNS = (r"\bchoose\b", r"\bdecide\b", r"\bpick\b", r"\bselect\b")
OTHER_PERSON_PATTERNS = (r"\bask\b", r"\bsend\b", r"\bmessage\b", r"\bcall\b")
THINKING_PATTERNS = (r"\bthink\b", r"\bbrainstorm\b", r"\bimagine\b")


def check(action: str, state: dict) -> dict:
    """Apply the five product constraints without calling a model."""
    text = action.strip().lower()
    reasons: list[str] = []
    minutes = int(state.get("minutes", 5))
    under_5 = minutes <= 5 and not re.search(r"\b(?:10|15|20|30|hour)\s*(?:minutes?|mins?)\b", text)
    physical = not any(re.search(pattern, text) for pattern in THINKING_PATTERNS)
    no_decision = not any(re.search(pattern, text) for pattern in DECISION_PATTERNS)
    solo = not any(re.search(pattern, text) for pattern in OTHER_PERSON_PATTERNS)
    scope_safe = not any(re.search(rf"\b{re.escape(word)}(?:ing|ed|s)?\b", text) for word in SCOPE_BLOCKLIST)
    requires_new_skill = any(re.search(rf"\b{tool}\b", text) for tool in TOOL_NAMES)
    if not under_5:
        reasons.append("takes_more_than_5_minutes")
    if not physical:
        reasons.append("not_physical")
    if not no_decision:
        reasons.append("needs_decision")
    if not solo:
        reasons.append("needs_other_person")
    if not scope_safe:
        reasons.append("reveals_scope")
    if requires_new_skill:
        reasons.append("needs_new_skill")
    return {
        "under_5_min": under_5,
        "physical": physical,
        "no_decision": no_decision,
        "solo": solo,
        "scope_safe": scope_safe and not requires_new_skill,
        "requires_new_skill": requires_new_skill,
        "passes": not reasons,
        "fail_reasons": reasons,
    }
