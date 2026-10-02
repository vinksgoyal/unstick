from app.constraints import check

STATE = {"minutes": 5}


def test_safe_physical_actions():
    actions = ["Open a note and type one title", "Save one file", "Move one photo", "Rename one file", "Copy one sentence",
               "Paste one sentence", "Print one page", "Delete one duplicate", "Archive one email", "Take a screenshot",
               "Label one folder"]
    assert all(check(action, STATE)["passes"] for action in actions)


def test_unsafe_actions():
    actions = ["Build a portfolio", "Design a homepage", "Plan the project", "Learn Figma", "Research galleries",
               "Decide on a color", "Choose a font", "Sketch a layout", "Outline the site", "Make a roadmap",
               "Think about the idea", "Ask a friend for feedback", "Spend 15 minutes organizing"]
    assert all(not check(action, STATE)["passes"] for action in actions)
