from app.agents.base import ReviewAgent


class GrammarAgent(ReviewAgent):
    """Checks grammar, spelling and punctuation."""

    name = "grammar"
