from app.agents.base_agent import BaseAgent


class GrammarAgent(BaseAgent):
    prompt_file = "grammar_prompt.txt"

    def run(self, state: dict):
        result = super().run(state)
        state["grammar_result"] = result
        return state