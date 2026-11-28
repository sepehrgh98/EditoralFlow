"""Send a full trace of one public SciFact development claim to LangSmith."""

import argparse
import asyncio
import json
from uuid import uuid4

from langsmith import Client, tracing_context

from app.core.config import DEFAULT_CORPUS_PATH, Settings
from app.llm.factory import build_llm_client
from app.main import build_fact_check


def load_claim(claim_id: int) -> str:
    path = DEFAULT_CORPUS_PATH.with_name("claims_dev.jsonl")
    with path.open(encoding="utf-8") as claims:
        for line in claims:
            record = json.loads(line)
            if record["id"] == claim_id:
                return record["claim"]
    raise ValueError(f"No SciFact development claim with ID {claim_id}")


async def trace_claim(claim_id: int, article: str, project: str) -> None:
    settings = Settings(corpus_path=DEFAULT_CORPUS_PATH)
    graph = build_fact_check(settings, build_llm_client(settings))
    run_id = uuid4()
    client = Client(hide_inputs=False, hide_outputs=False, hide_metadata=False)
    try:
        with tracing_context(client=client, enabled=True, project_name=project):
            final = await graph.ainvoke(
                {"article": article},
                config={
                    "run_id": run_id,
                    "run_name": f"Public SciFact claim {claim_id}",
                    "tags": ["public-scifact"],
                    "max_concurrency": settings.fact_check_max_concurrency,
                },
            )
    finally:
        client.flush()

    print(f"LangSmith project: {project}")
    print(f"Trace ID: {run_id}")
    print(final["response"].model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("claim_id", type=int, help="Claim ID in the public SciFact dev split")
    parser.add_argument("--project", default="editoralflow-local", help="LangSmith tracing project")
    args = parser.parse_args()
    try:
        article = load_claim(args.claim_id)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(f"{exc}. Run `make data` to install SciFact.")
    asyncio.run(trace_claim(args.claim_id, article, args.project))


if __name__ == "__main__":
    main()
