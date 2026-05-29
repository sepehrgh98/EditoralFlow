from abc import ABC
import json

from app.models.agent_result import AgentResult
from app.services.llm.base import BaseLLMService
from app.utils.prompt_loader import load_prompt


class BaseAgent(ABC):
    prompt_file: str = ""

    def __init__(self, llm_service: BaseLLMService):
        self.llm = llm_service

    def build_prompt(self, article: str) -> str:
        template = load_prompt(self.prompt_file)
        return template.format(article=article)

    def clean_json_response(self, response: str) -> str:
        response = response.strip()

        if response.startswith("```json"):
            response = response.removeprefix("```json").strip()

        if response.startswith("```"):
            response = response.removeprefix("```").strip()

        if response.endswith("```"):
            response = response.removesuffix("```").strip()

        return response

    def run(self, state: dict) -> AgentResult:
        article = state["article"]

        prompt = self.build_prompt(article)

        response = self.llm.generate(prompt)

        cleaned_response = self.clean_json_response(response)

        data = json.loads(cleaned_response)

        return AgentResult(**data)