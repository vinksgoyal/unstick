# Unstick

Unstick turns a stalled creative goal into exactly three small, physical actions.
It is for people who freeze when a tool exposes the whole mountain.

Every action must be under five minutes, physical, require no decision, require
no other person, and hide the scope of the larger project. The rule checker is
the ground truth; model output must pass it before it is shown.

## Privacy

The goal text, notes, and abandoned drafts are content and stay in local SQLite.
They never go to Backboard, Render, or another remote service. Backboard is
reserved for abstract behavioural signals (`goal_id`, `energy`, `minutes`,
`time_bucket`, `action_type`, `completed`) so it can learn which action types
work in a context. See [docs/architecture.md](docs/architecture.md).

## Local setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
ollama pull gemma2:2b
uvicorn app.main:app --reload
```

Open `frontend/index.html`. If Ollama is unavailable, the API uses safe,
deterministic starter actions and reports model availability at `/api/health`.

## Deployment

`render.yaml` defines an API web service and a static frontend. Set
`ENV=production`, `TINKER_MODEL_ID`, and the verified Backboard credentials only
after wiring their current official SDK adapters. Tinker documentation is at
https://tinker-docs.thinkingmachines.ai/; Backboard documentation is at
https://docs.backboard.io/. No endpoint is guessed in this scaffold.

## Training and evaluation

Seed examples are in `training/seed_dataset.jsonl`; the label helper appends
hand labels. `training/tinker_finetune.py` and `eval/run_eval.py` are safe
placeholders until a supported Tinker recipe and held-out set are supplied.

## Screenshot

_Add a screenshot of the three-card experience here._
