"""The search interface every retriever implements, and what a search returns."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.retrieval.corpus import Document


class Passage(BaseModel):
    """One search result: a source document and how well it matched (higher is better)."""

    document: Document
    score: float


class Retriever(ABC):
    """Finds the documents most relevant to a query.

    Async like the LLM layer: BM25 is in memory, but later retrievers (vector search,
    Phase 3) call a database.
    """

    @abstractmethod
    async def search(self, query: str, k: int = 3) -> list[Passage]:
        """Return at most k passages, best first. Empty if nothing is relevant."""
