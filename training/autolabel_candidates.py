"""Auto-label generated candidates using app.constraints.check.

Anything the rule-checker rejects gets labeled unsafe with the rule's
failure reason. Anything it accepts stays unlabeled so I can review it
by hand — those are the interesting ones.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.constraints import check  # noqa: E402


def main() -> None:
    src = Path("training/candidates.jsonl")
    out_unsafe = Path("training/autolabeled_unsafe.jsonl")
    out_review = Path("training/needs_review.jsonl")

    safe_count = 0
    unsafe_count = 0

    with src.open() as f, out_unsafe.open("w") as u, out_review.open("w") as r:
        for line in f:
            rec = json.loads(line)
            verdict = check(rec["action"], rec.get("state", {}))
            if not verdict["passes"]:
                # force it into a fail_type the schema allows
                reasons = verdict["fail_reasons"]
                if "needs_new_skill" in reasons:
                    ft = "needs_new_skill"
                elif "reveals_scope" in reasons:
                    ft = "reveals_scope"
                elif "needs_decision" in reasons:
                    ft = "needs_decision"
                elif "not_physical" in reasons:
                    ft = "not_physical"
                elif "needs_other_person" in reasons:
                    ft = "needs_other_person"
                else:
                    ft = "off_topic"
                rec["scope_safe"] = False
                rec["fail_type"] = ft
                rec["rewrite"] = None
                u.write(json.dumps(rec) + "\n")
                unsafe_count += 1
            else:
                r.write(json.dumps(rec) + "\n")
                safe_count += 1

    print(f"wrote {unsafe_count} auto-labeled unsafe rows to {out_unsafe}")
    print(f"wrote {safe_count} rows that need your review to {out_review}")


if __name__ == "__main__":
    main()
