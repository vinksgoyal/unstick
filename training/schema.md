# Training schema

Each JSONL record contains `goal`, `state`, `action`, `scope_safe`, `fail_type`, and `rewrite`.
`fail_type` is one of `reveals_scope`, `needs_new_skill`, `needs_decision`,
`not_physical`, or `needs_other_person`; safe examples use `null`.
