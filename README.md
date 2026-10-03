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

`APP_MODE=local` (the default) generates candidate actions with local Ollama and
classifies them with the Tinker fine-tuned sampler when `TINKER_SAMPLER_PATH`
is configured. Without Tinker, classification safely falls back to `safe`.
Set `APP_MODE=hosted` to generate five candidates with Tinker as well as use
the fine-tuned classifier. The sampler path uses the format
`tinker://<id>/sampler_weights/unstick-classifier`.

## Deployment

`render.yaml` defines an API web service and a static frontend. Set
`ENV=production`, `APP_MODE=hosted`, `TINKER_SAMPLER_PATH`, and the verified
Backboard credentials. Tinker documentation is at
https://tinker-docs.thinkingmachines.ai/; Backboard documentation is at
https://docs.backboard.io/.

## Fine-tuned classifier

The base Qwen3-8B classifier reached 27% accuracy on the held-out set; the
fine-tuned sampler reached 70% accuracy. The training recipe and label-space
definition are in
[training/tinker_finetune.py](training/tinker_finetune.py).

| Model | Accuracy |
|---|---:|
| Base Qwen3-8B | 27% |
| Fine-tuned Tinker sampler | 70% |

## Training and evaluation

Seed examples are in `training/seed_dataset.jsonl`; the label helper appends
hand labels. `training/tinker_finetune.py` contains the LoRA training recipe,
and `eval/run_eval.py` evaluates the base and fine-tuned samplers on the
held-out set.

## Screenshot

_Add a screenshot of the three-card experience here._
