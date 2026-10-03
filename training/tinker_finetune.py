"""Fine-tune Qwen3-8B on Unstick labels via Tinker SDK.

Task: given (goal, action), predict a label:
  safe
  unsafe:reveals_scope
  unsafe:needs_new_skill
  unsafe:needs_decision
  unsafe:not_physical
  unsafe:needs_other_person
  unsafe:off_topic

Uses LoRA SFT with loss masked to the answer tokens only.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

import tinker
from dotenv import load_dotenv

load_dotenv()

BASE_MODEL = os.getenv("TINKER_BASE_MODEL", "Qwen/Qwen3-8B")
LORA_RANK = int(os.getenv("TINKER_LORA_RANK", "16"))
LEARNING_RATE = float(os.getenv("TINKER_LR", "1e-4"))
EPOCHS = int(os.getenv("TINKER_EPOCHS", "3"))

LABELS = [
    "safe",
    "unsafe:reveals_scope",
    "unsafe:needs_new_skill",
    "unsafe:needs_decision",
    "unsafe:not_physical",
    "unsafe:needs_other_person",
    "unsafe:off_topic",
]


def format_prompt(goal: str, action: str) -> str:
    return (
        "You are classifying whether an action helps a user make progress on "
        "their stated goal without overwhelming them.\n\n"
        f"Goal: {goal}\n"
        f"Action: {action}\n\n"
        "Reply with exactly one of: safe, unsafe:reveals_scope, "
        "unsafe:needs_new_skill, unsafe:needs_decision, unsafe:not_physical, "
        "unsafe:needs_other_person, unsafe:off_topic\n"
        "Label:"
    )


def label_from_record(rec: dict) -> str:
    if rec["scope_safe"]:
        return "safe"
    return f"unsafe:{rec['fail_type']}"


def build_datum(tokenizer, goal: str, action: str, label: str):
    prompt_text = format_prompt(goal, action)
    answer_text = " " + label

    prompt_ids = tokenizer.encode(prompt_text)
    answer_ids = tokenizer.encode(answer_text)
    full_ids = prompt_ids + answer_ids

    model_input = tinker.types.ModelInput.from_ints(full_ids[:-1])
    n_prefix = len(prompt_ids) - 1
    weights = [0.0] * n_prefix + [1.0] * len(answer_ids)
    target_tokens = full_ids[1:]

    assert len(model_input.to_ints()) == len(target_tokens) == len(weights)
    return tinker.types.Datum(
        model_input=model_input,
        loss_fn_inputs={
            "weights": weights,
            "target_tokens": target_tokens,
        },
    )

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, default=Path("training/train.jsonl"))
    parser.add_argument("--held-out", type=Path, default=Path("training/held_out.jsonl"))
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--output", type=Path, default=Path("training/tinker_run.json"))
    args = parser.parse_args()

    train = [
        json.loads(line)
        for line in args.train.read_text().splitlines()
        if line.strip()
    ]
    print(f"Loaded {len(train)} training rows.")

    service_client = tinker.ServiceClient()
    training_client = await service_client.create_lora_training_client_async(
        base_model=BASE_MODEL, rank=LORA_RANK
    )
    tokenizer = training_client.get_tokenizer()
    print(f"Training client ready. Base model: {BASE_MODEL}, LoRA rank: {LORA_RANK}")

    datums = [build_datum(tokenizer, r["goal"], r["action"], label_from_record(r)) for r in train]

    bs = args.batch_size
    num_batches = (len(datums) + bs - 1) // bs
    step = 0
    for epoch in range(EPOCHS):
        for i in range(0, len(datums), bs):
            batch = datums[i : i + bs]
            await training_client.forward_backward_async(
                data=batch, loss_fn="cross_entropy"
            )
            await training_client.optim_step_async(
                tinker.types.AdamParams(learning_rate=LEARNING_RATE)
            )
            step += 1
            if step % 5 == 0 or step == num_batches * EPOCHS:
                print(f"epoch {epoch + 1} step {step}/{num_batches * EPOCHS}")

    print("Training done. Saving sampler checkpoint...")
    sampler_future = await training_client.save_weights_for_sampler_async(name="unstick-classifier")
    sampler = await sampler_future.result_async()
    print(f"Sampler checkpoint path: {sampler.path}")
    print(f"Playground URL: {sampler.get_playground_url()}")

    args.output.write_text(json.dumps({
        "base_model": BASE_MODEL,
        "lora_rank": LORA_RANK,
        "learning_rate": LEARNING_RATE,
        "epochs": EPOCHS,
        "train_rows": len(train),
        "sampler_path": sampler.path,
        "playground_url": sampler.get_playground_url(),
    }, indent=2))
    print(f"Wrote run metadata to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
