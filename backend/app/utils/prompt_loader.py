from pathlib import Path


def load_prompt(prompt_name: str) -> str:

    base_path = Path(__file__).resolve().parent.parent

    prompt_path = (
        base_path / "agents" / "prompts" / prompt_name
    )

    with open(prompt_path, "r") as f:
        return f.read()