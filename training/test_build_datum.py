import asyncio
import json
import sys
from pathlib import Path

import pytest

tinker = pytest.importorskip("tinker")

sys.path.insert(0, str(Path(__file__).parent))
from tinker_finetune import build_datum, format_prompt, label_from_record  # noqa: E402


def test_build_datum_lengths_and_loss_mask() -> None:
    async def load_tokenizer():
        service_client = tinker.ServiceClient()
        training_client = await service_client.create_lora_training_client_async(
            base_model="Qwen/Qwen3-8B", rank=16
        )
        tokenizer = training_client.get_tokenizer()
        del training_client
        return tokenizer

    tokenizer = asyncio.run(load_tokenizer())
    record = json.loads(Path("training/train.jsonl").read_text().splitlines()[0])
    datum = build_datum(
        tokenizer,
        record["goal"],
        record["action"],
        label_from_record(record),
    )

    def _to_list(t):
        if hasattr(t, "to_list"):
            return t.to_list()
        if hasattr(t, "data"):
            return list(t.data)
        return list(t)

    def _len(t):
        return len(_to_list(t))

    assert (
        len(datum.model_input.to_ints())
        == _len(datum.loss_fn_inputs["target_tokens"])
        == _len(datum.loss_fn_inputs["weights"])
    )
    prompt_length = len(tokenizer.encode(format_prompt(record["goal"], record["action"])))
    weights = _to_list(datum.loss_fn_inputs["weights"])
    assert weights[: prompt_length - 1] == [0.0] * (prompt_length - 1)
    assert weights[prompt_length - 1:] == [1.0] * (len(weights) - prompt_length + 1)
