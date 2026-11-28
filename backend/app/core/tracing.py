"""LangSmith configuration for the application's graph entry points.

Tracing is opt-in (LANGSMITH_TRACING=true in the backend's environment). When it is on,
every Review and Fact-check trace sends full inputs, outputs and error messages: draft
text, prompts, retrieved abstracts and model answers (ADR 0012).
"""

from contextlib import nullcontext
from functools import cache

from langsmith import Client, tracing_context
from langsmith.utils import tracing_is_enabled


@cache
def tracing_client() -> Client:
    """One client for the root run and all nested spans. Nothing is hidden."""
    return Client()


def graph_tracing():
    """Send the graph run and its nested spans through the shared client when tracing is on."""
    if tracing_is_enabled():
        return tracing_context(client=tracing_client())
    return nullcontext()
