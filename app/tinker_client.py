import asyncio
import logging
import os
import re
from typing import Any

try:
    import tinker
    from training.tinker_finetune import format_prompt
    from eval.run_eval import parse_prediction
except ModuleNotFoundError:
    tinker = None

    # Keep the app importable without the optional Tinker SDK. This mirrors
    # training/tinker_finetune.py until the SDK is installed.
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

    def parse_prediction(response: str) -> str | None:
        labels = (
            "unsafe:needs_other_person",
            "unsafe:reveals_scope",
            "unsafe:needs_new_skill",
            "unsafe:needs_decision",
            "unsafe:not_physical",
            "unsafe:off_topic",
            "safe",
        )
        return next((label for label in labels if label in response), None)


logger = logging.getLogger(__name__)
TINKER_SAMPLER_PATH = os.getenv("TINKER_SAMPLER_PATH")
BASE_MODEL = "Qwen/Qwen3-8B"


def _fallback() -> dict[str, Any]:
    return {"scope_safe": True, "fail_type": None, "raw": "fallback"}


async def classify(goal: str, action: str) -> dict[str, Any]:
    if not TINKER_SAMPLER_PATH or tinker is None:
        logger.warning("Tinker sampler is not configured; using classifier fallback")
        return _fallback()

    try:
        service_client = tinker.ServiceClient()
        sampling_client = service_client.create_sampling_client(
            model_path=TINKER_SAMPLER_PATH
        )
        tokenizer_client = await service_client.create_lora_training_client_async(
            base_model=BASE_MODEL, rank=16
        )
        tokenizer = tokenizer_client.get_tokenizer()
        model_input = tinker.types.ModelInput.from_ints(
            tokenizer.encode(format_prompt(goal, action))
        )
        result = await sampling_client.sample_async(
            prompt=model_input,
            num_samples=1,
            sampling_params=tinker.types.SamplingParams(
                max_tokens=16, temperature=0.0
            ),
        )
        raw = tokenizer.decode(result.sequences[0].tokens)
        label = parse_prediction(raw)
        if label is None:
            raise ValueError(f"Tinker response did not contain a known label: {raw!r}")
        if label == "safe":
            return {"scope_safe": True, "fail_type": None, "raw": raw}
        return {"scope_safe": False, "fail_type": label.removeprefix("unsafe:"), "raw": raw}
    except Exception as exc:
        logger.warning("Tinker classification failed; using fallback: %s", exc)
        return _fallback()


def classify_sync(goal: str, action: str) -> dict[str, Any]:
    return asyncio.run(classify(goal, action))


async def _sample_candidates(goal: str) -> list[str]:
    service_client = tinker.ServiceClient()
    if TINKER_SAMPLER_PATH:
        sampling_client = service_client.create_sampling_client(
            model_path=TINKER_SAMPLER_PATH
        )
    else:
        sampling_client = service_client.create_sampling_client(base_model=BASE_MODEL)
    tokenizer_client = await service_client.create_lora_training_client_async(
        base_model=BASE_MODEL, rank=16
    )
    tokenizer = tokenizer_client.get_tokenizer()
    prompt = (
        "Return exactly five short candidate actions, one per line, for this goal. "
        "Each action must be physical, take five minutes or less, require no choice "
        "or other person, and reveal no project scope.\n"
        f"Goal: {goal}\n"
    )
    model_input = tinker.types.ModelInput.from_ints(tokenizer.encode(prompt))
    result = await sampling_client.sample_async(
        prompt=model_input,
        num_samples=1,
        sampling_params=tinker.types.SamplingParams(max_tokens=128, temperature=0.0),
    )
    raw = tokenizer.decode(result.sequences[0].tokens)
    return [
        re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
        for line in raw.splitlines()
        if line.strip()
    ][:5]


def sample_candidates_sync(goal: str) -> list[str]:
    if tinker is None:
        logger.warning("Tinker SDK is unavailable; using candidate fallback")
        return []
    try:
        return asyncio.run(_sample_candidates(goal))
    except Exception as exc:
        logger.warning("Tinker candidate generation failed: %s", exc)
        return []
