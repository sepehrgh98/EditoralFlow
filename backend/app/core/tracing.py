"""LangSmith configuration for the application's graph entry points."""

from contextlib import nullcontext
from functools import cache
from typing import Any

from langsmith import Client, tracing_context
from langsmith.utils import tracing_is_enabled

_TRACE_METADATA = frozenset(
    {
        "claim_id",
        "retrieved_documents",
        "model",
        "latency_ms",
        "verdict",
        "citation_ids",
    }
)


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    if "error" in data:
        return {"error": "Run failed. See backend logs for details."}
    return {key: value for key, value in data.items() if key in _TRACE_METADATA}


@cache
def tracing_client() -> Client:
    return Client(
        hide_inputs=True,
        hide_outputs=True,
        hide_metadata=False,
        anonymizer=_redact,
    )


def graph_tracing():
    """Use the same masked client for the root and nested spans when tracing is enabled."""
    if tracing_is_enabled():
        return tracing_context(client=tracing_client())
    return nullcontext()
