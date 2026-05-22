import json
import os

from utils.settings import TARGET_TASKS


def load_examples(examples_dir: str) -> dict:
    examples = {}
    for task in TARGET_TASKS:
        path = os.path.join(examples_dir, f"{task}.json")
        if not os.path.exists(path):
            examples[task] = []
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            examples[task] = []
            continue

        if isinstance(data, list):
            examples[task] = [x for x in data if x]
        elif isinstance(data, dict) and data:
            examples[task] = [data]
        else:
            examples[task] = []
    return examples


def format_examples(items: list) -> str:
    if not items:
        return "(no reference examples available)"
    blocks = []
    for i, ex in enumerate(items, 1):
        blocks.append(
            f"### Example {i}:\n{json.dumps(ex, indent=2, ensure_ascii=False)}"
        )
    return "\n\n".join(blocks)
