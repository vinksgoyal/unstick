import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", action="store_true")
    parser.parse_args()
    print("| Model | Scope-safe Acc | Fail-type F1 | Rewrite Quality | Latency | Cost/1k |")
    print("|---|---:|---:|---:|---:|---:|")
    print("| base-gemma2 | n/a | n/a | n/a | n/a | n/a |")
    print("| tinker-finetuned | n/a | n/a | n/a | n/a | n/a |")


if __name__ == "__main__":
    main()
