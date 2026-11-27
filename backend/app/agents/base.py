"""BaseAgent: the shared work of every review agent.

An agent is a system prompt (its job description), a user prompt template (where the
article goes), an answer shape and a model tier. BaseAgent loads the prompts, fills in
the article and asks the LLM for a structured answer.
"""

from pathlib import Path
from typing import ClassVar

from app.llm.base import LLMClient, LLMResponse, ModelTier
from app.models.review import AgentResult

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
ARTICLE_SLOT = "{article}"


def load_prompt(agent: str, kind: str) -> str:
    """Read prompts/<agent>/<kind>.txt, for example prompts/grammar/system.txt."""
    path = PROMPTS_DIR / agent / f"{kind}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


class BaseAgent:
    """Subclasses set `name` (their folder under prompts/) and may change `tier`."""

    name: ClassVar[str]
    output_schema: ClassVar[type[AgentResult]] = AgentResult
    tier: ClassVar[ModelTier] = "fast"

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        # Loaded once, so a missing or broken prompt fails at startup, not mid-review
        self.system_prompt = load_prompt(self.name, "system")
        self.user_template = load_prompt(self.name, "user")
        if ARTICLE_SLOT not in self.user_template:
            raise ValueError(f"prompts/{self.name}/user.txt must contain {ARTICLE_SLOT}")

    def build_user_prompt(self, article: str) -> str:
        """Put the article into the user prompt template."""
        return self.user_template.replace(ARTICLE_SLOT, article)

    async def review(self, article: str) -> LLMResponse[AgentResult]:
        """Review the article. Returns the result and the LLM usage of the call."""
        return await self._llm.generate_structured(
            self.build_user_prompt(article),
            self.output_schema,
            system=self.system_prompt,
            tier=self.tier,
        )
