"""Fast keyboard-driven labeler for Unstick candidates.

Controls:
  y = scope-safe
  n = not scope-safe (then pick fail type with 1-5)
  s = skip
  b = back one line
  q = quit and save

Fail types:
  1 reveals_scope
  2 needs_new_skill
  3 needs_decision
  4 not_physical
  5 needs_other_person
"""
import argparse
import json
from pathlib import Path

FAIL_TYPES = {
    "1": "reveals_scope",
    "2": "needs_new_skill",
    "3": "needs_decision",
    "4": "not_physical",
    "5": "needs_other_person",
}

RULE = "-" * 70


def prompt(msg: str) -> str:
    return input(msg).strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("training/labeled.jsonl"))
    args = parser.parse_args()

    done_keys: set[tuple[str, str]] = set()
    if args.output.exists():
        for line in args.output.read_text().splitlines():
            try:
                rec = json.loads(line)
                done_keys.add((rec["goal"], rec["action"]))
            except Exception:
                pass

    items = []
    for line in args.input.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (rec["goal"], rec["action"]) in done_keys:
            continue
        items.append(rec)

    total = len(items)
    if total == 0:
        print("Nothing to label — all rows already labeled.")
        return

    print(f"\nLabeling {total} candidates. Press ? for controls.\n")
    out = args.output.open("a")
    idx = 0
    while idx < total:
        rec = items[idx]
        state = rec.get("state", {})
        print(RULE)
        print(f"[{idx + 1}/{total}]  goal: {rec['goal']}")
        print(f"           state: {state}")
        print(f"           action: {rec['action']}")
        print(RULE)

        choice = prompt("[y] safe  [n] unsafe  [s] skip  [q] quit: ")

        if choice == "q":
            break
        if choice == "s":
            idx += 1
            continue

        if choice == "y":
            rec["scope_safe"] = True
            rec["fail_type"] = None
            rec["rewrite"] = None
        elif choice == "n":
            ft = prompt("fail type [1-5]: ")
            if ft not in FAIL_TYPES:
                print("  invalid, try again")
                continue
            rec["scope_safe"] = False
            rec["fail_type"] = FAIL_TYPES[ft]
            rw = prompt("rewrite (enter to skip): ")
            rec["rewrite"] = rw or None
        else:
            print("  invalid, try again")
            continue

        out.write(json.dumps(rec) + "\n")
        out.flush()
        idx += 1

    out.close()
    print("\nSaved. Run again to resume.")


if __name__ == "__main__":
    main()
