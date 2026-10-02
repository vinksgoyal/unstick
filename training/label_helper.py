import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("labeled.jsonl"))
    args = parser.parse_args()
    with args.input.open() as source, args.output.open("a") as target:
        for line in source:
            item = json.loads(line)
            print(f"\n{item.get('goal')}\n{item.get('action')}")
            safe = input("scope-safe? [y/n] ").lower() == "y"
            item.update({"scope_safe": safe, "fail_type": None if safe else input("fail type: "), "rewrite": None if safe else input("rewrite (optional): ")})
            target.write(json.dumps(item) + "\n")


if __name__ == "__main__":
    main()
