from pathlib import Path


def main() -> None:
    dataset = Path("tests/fixtures/gold_qa.json")
    if not dataset.exists():
        print("No gold QA dataset found yet.")
        return
    print(f"Evaluation dataset ready: {dataset}")
    print("Run API-backed retrieval comparisons after documents are indexed.")


if __name__ == "__main__":
    main()

