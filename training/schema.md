# Training schema

Each JSONL record contains `goal`, `state`, `action`, `scope_safe`, `fail_type`, and `rewrite`.

`fail_type` is one of:

- `reveals_scope` — the action implies how much work exists
- `needs_new_skill` — requires learning a tool the user hasn't used
- `needs_decision` — asks the user to choose
- `not_physical` — a mental action ("think about", "reflect on")
- `needs_other_person` — depends on someone else
- `off_topic` — does not advance the stated goal at all

Safe examples use `null` for both `fail_type` and `rewrite`.
