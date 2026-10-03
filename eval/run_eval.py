import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import tinker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training.tinker_finetune import LABELS, format_prompt, label_from_record  # noqa: E402

BASE_MODEL = "Qwen/Qwen3-8B"


def parse_prediction(response: str) -> str | None:
    for label in sorted(LABELS, key=len, reverse=True):
        if label in response:
            return label
    return None


def binary_f1(expected: list[bool], predicted: list[bool]) -> float:
    true_positive = sum(actual and guess for actual, guess in zip(expected, predicted))
    false_positive = sum(not actual and guess for actual, guess in zip(expected, predicted))
    false_negative = sum(actual and not guess for actual, guess in zip(expected, predicted))
    if true_positive == 0:
        return 0.0
    return 2 * true_positive / (2 * true_positive + false_positive + false_negative)


async def run_eval(model_path: str | None, output_path: Path) -> tuple[str, float, float, float, int, float]:
    rows = [
        json.loads(line)
        for line in Path("training/held_out.jsonl").read_text().splitlines()
        if line.strip()
    ]
    service_client = tinker.ServiceClient()
    sampling_client = (
        service_client.create_sampling_client(model_path=model_path)
        if model_path
        else service_client.create_sampling_client(base_model=BASE_MODEL)
    )
    tokenizer_client = await service_client.create_lora_training_client_async(
        base_model=BASE_MODEL, rank=16
    )
    tokenizer = tokenizer_client.get_tokenizer()
    params = tinker.types.SamplingParams(max_tokens=16, temperature=0.0)

    expected_labels = [label_from_record(row) for row in rows]
    predictions: list[str | None] = []
    prediction_records = []
    started = time.perf_counter()
    for row, expected in zip(rows, expected_labels):
        prompt = format_prompt(row["goal"], row["action"])
        model_input = tinker.types.ModelInput.from_ints(tokenizer.encode(prompt))
        result = await sampling_client.sample_async(
            prompt=model_input, num_samples=1, sampling_params=params
        )
        response = tokenizer.decode(result.sequences[0].tokens)
        prediction = parse_prediction(response)
        predictions.append(prediction)
        prediction_records.append({
            "goal": row["goal"],
            "action": row["action"],
            "expected": expected,
            "prediction": prediction,
            "response": response,
        })
    elapsed = time.perf_counter() - started

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(record) for record in prediction_records) + "\n"
    )

    expected_safe = [label == "safe" for label in expected_labels]
    predicted_safe = [label == "safe" for label in predictions]
    accuracy = sum(expected == predicted for expected, predicted in zip(expected_labels, predictions)) / len(rows)
    safe_f1 = binary_f1(expected_safe, predicted_safe)
    fail_f1 = binary_f1(
        [not value for value in expected_safe],
        [not value for value in predicted_safe],
    )
    model_name = "fine-tuned" if model_path else "base"
    return model_name, accuracy, safe_f1, fail_f1, len(rows), elapsed


def print_table(result: tuple[str, float, float, float, int, float]) -> None:
    model, accuracy, safe_f1, fail_f1, rows, elapsed = result
    print("| Model | Accuracy | Safe-F1 | Fail-F1 | Rows | Elapsed |")
    print("|---|---:|---:|---:|---:|---:|")
    print(f"| {model} | {accuracy:.4f} | {safe_f1:.4f} | {fail_f1:.4f} | {rows} | {elapsed:.2f}s |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--model")
    args = parser.parse_args()
    output_path = Path("eval/predictions_ft.jsonl" if args.model else "eval/predictions_base.jsonl")
    result = asyncio.run(run_eval(args.model, output_path))
    print_table(result)


if __name__ == "__main__":
    main()
