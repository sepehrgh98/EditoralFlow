from app.agents.base_agent import BaseAgent


class StyleAgent(BaseAgent):
    prompt_file = "style_prompt.txt"

    def run(self, state: dict):
        result = super().run(state)
        state["style_result"] = result
        return state