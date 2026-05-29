# backend/app/services/llm/anthropic_service.py

import os

import anthropic

from app.services.llm.base import BaseLLMService


class AnthropicService(BaseLLMService):

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:

        response = self.client.messages.create(
            model="claude-sonnet-4-0",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text