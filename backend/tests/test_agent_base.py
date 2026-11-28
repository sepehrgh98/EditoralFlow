"""The generic BaseAgent, with made-up agents and prompts written into a temp folder."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from app.agents.base import BaseAgent
from tests.fakes import FakeLLM


class Answer(BaseModel):
    verdict: str


def write_prompts(folder: Path, name: str, user: str) -> None:
    (folder / name).mkdir(parents=True)
    (folder / name / "system.txt").write_text("You check claims.")
    (folder / name / "user.txt").write_text(user)


def make_agent_class(prompts: Path, slots: tuple[str, ...]) -> type[BaseAgent[Answer]]:
    class TwoSlotAgent(BaseAgent[Answer]):
        name = "two_slot"
        output_schema = Answer
        prompts_dir = prompts
        tier = "strong"

    TwoSlotAgent.slots = slots
    return TwoSlotAgent


@pytest.fixture
def prompts(tmp_path: Path) -> Path:
    write_prompts(tmp_path, "two_slot", "Claim: {claim}\n\nSources:\n{passages}")
    return tmp_path


async def test_fills_named_slots_and_uses_its_own_schema_and_tier(prompts: Path) -> None:
    llm = FakeLLM([{"verdict": "supported"}])
    agent = make_agent_class(prompts, ("claim", "passages"))(llm)

    response = await agent.run(claim="Statins work.", passages="[1] Deaths fell.")

    assert response.content == Answer(verdict="supported")
    call = llm.calls[0]
    assert call.prompt == "Claim: Statins work.\n\nSources:\n[1] Deaths fell."
    assert call.system == "You check claims."
    assert call.schema is Answer
    assert call.tier == "strong"


def test_prompt_missing_a_declared_slot_fails_at_creation(prompts: Path) -> None:
    agent_class = make_agent_class(prompts, ("claim", "passages", "article"))

    with pytest.raises(ValueError, match="exactly the slots"):
        agent_class(FakeLLM())


def test_prompt_with_an_undeclared_slot_fails_at_creation(prompts: Path) -> None:
    agent_class = make_agent_class(prompts, ("claim",))

    with pytest.raises(ValueError, match="found \\['claim', 'passages'\\]"):
        agent_class(FakeLLM())


@pytest.mark.parametrize(
    "values",
    [{"claim": "x"}, {"claim": "x", "passages": "y", "extra": "z"}, {}],
)
def test_missing_or_extra_values_are_rejected(prompts: Path, values: dict[str, str]) -> None:
    agent = make_agent_class(prompts, ("claim", "passages"))(FakeLLM())

    with pytest.raises(ValueError, match="needs values"):
        agent.build_user_prompt(**values)


def test_slot_like_text_inside_a_value_is_left_as_written(prompts: Path) -> None:
    agent = make_agent_class(prompts, ("claim", "passages"))(FakeLLM())

    prompt = agent.build_user_prompt(claim="mentions {passages}", passages="and {claim}")

    assert prompt == "Claim: mentions {passages}\n\nSources:\nand {claim}"


def test_missing_prompt_folder_fails_at_creation(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        make_agent_class(tmp_path, ("claim",))(FakeLLM())
