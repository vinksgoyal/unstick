import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("goals", type=Path)
    parser.add_argument("--output", type=Path, default=Path("candidates.jsonl"))
    args = parser.parse_args()
    with args.goals.open() as source, args.output.open("w") as target:
        for line in source:
            goal = line.strip()
            if goal:
                target.write(json.dumps({"goal": goal, "action": ""}) + "\n")


if __name__ == "__main__":
    main()
