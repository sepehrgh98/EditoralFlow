from app.agents.grammar_agent import GrammarAgent
from app.agents.style_agent import StyleAgent

from app.services.llm.factory import get_llm_service


class ReviewWorkflow:

    def __init__(self):

        llm = get_llm_service("anthropic")

        self.grammar_agent = GrammarAgent(llm)
        self.style_agent = StyleAgent(llm)

    def run(self, article: str):

        state = {
            "article": article
        }

        state = self.grammar_agent.run(state)

        state = self.style_agent.run(state)

        return state