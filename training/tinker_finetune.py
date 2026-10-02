"""Prepare a Tinker fine-tuning run.

The SDK's current training recipe must be wired after selecting a supported base
model. This intentionally avoids inventing an API call.
"""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--val", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.dataset.read_text().splitlines() if line]
    print(f"Loaded {len(records)} training records.")
    print("TODO: verify official Tinker SDK training recipe before submitting; no model was created.")


if __name__ == "__main__":
    main()
