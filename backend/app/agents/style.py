from app.agents.base import ReviewAgent


class StyleAgent(ReviewAgent):
    """Checks tone, clarity, readability and consistency."""

    name = "style"
