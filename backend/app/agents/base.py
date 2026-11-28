"""BaseAgent: the shared work of every agent.

An agent is a system prompt (its job description), a user prompt template with named
slots such as {article} or {claim}, an answer shape and a model tier. BaseAgent loads
the prompts, fills the slots and asks the LLM for an answer in that shape.
"""

import re
from pathlib import Path
from typing import ClassVar

from langsmith import trace
from pydantic import BaseModel

from app.llm.base import LLMClient, LLMResponse, ModelTier
from app.models.review import AgentResult

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
# A slot is a lowercase name in braces, e.g. {article} or {passages}
SLOT_PATTERN = re.compile(r"\{([a-z_]+)\}")


def load_prompt(agent: str, kind: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Read <prompts_dir>/<agent>/<kind>.txt, for example prompts/grammar/system.txt."""
    path = prompts_dir / agent / f"{kind}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


class BaseAgent[R: BaseModel]:
    """Subclasses set `name` (their prompt folder), `output_schema` and `slots`."""

    name: ClassVar[str]
    output_schema: type[R]
    slots: ClassVar[tuple[str, ...]]
    tier: ClassVar[ModelTier] = "fast"
    prompts_dir: ClassVar[Path] = PROMPTS_DIR

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        # Loaded and checked once, so a broken prompt fails at startup, not mid-request
        self.system_prompt = load_prompt(self.name, "system", self.prompts_dir)
        self.user_template = load_prompt(self.name, "user", self.prompts_dir)
        found = set(SLOT_PATTERN.findall(self.user_template))
        if found != set(self.slots):
            raise ValueError(
                f"prompts/{self.name}/user.txt must contain exactly the slots "
                f"{sorted(self.slots)}, found {sorted(found)}"
            )

    def build_user_prompt(self, **values: str) -> str:
        """Fill every slot. All slots are filled in one pass, so text inside a value that
        looks like a slot (e.g. an article containing "{claim}") is left as written."""
        if set(values) != set(self.slots):
            raise ValueError(
                f"{type(self).__name__} needs values for {sorted(self.slots)}, got {sorted(values)}"
            )
        return SLOT_PATTERN.sub(lambda match: values[match.group(1)], self.user_template)

    async def run(self, **values: str) -> LLMResponse[R]:
        """Fill the slots and ask the LLM. Returns the answer and the usage of the call."""
        prompt = self.build_user_prompt(**values)
        with trace("Generate structured answer", run_type="llm") as run:
            result = await self._llm.generate_structured(
                prompt,
                self.output_schema,
                system=self.system_prompt,
                tier=self.tier,
            )
            run.add_metadata({"model": result.usage.model, "latency_ms": result.usage.latency_ms})
        return result


class ReviewAgent(BaseAgent[AgentResult]):
    """An agent that reviews an article and returns score, issues and summary."""

    output_schema = AgentResult
    slots = ("article",)

    async def review(self, article: str) -> LLMResponse[AgentResult]:
        """Review the article. Returns the result and the LLM usage of the call."""
        return await self.run(article=article)
