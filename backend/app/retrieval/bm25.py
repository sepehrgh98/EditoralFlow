"""BM25 keyword search over the corpus, held in memory (ADR 0009)."""

import logging
import time
from typing import cast

import bm25s
import Stemmer

from app.retrieval.base import Passage, Retriever
from app.retrieval.corpus import Corpus

logger = logging.getLogger(__name__)


class BM25Retriever(Retriever):
    """Scores each document by shared words, weighting rare words more.

    Words are lowercased, stemmed ("reduces" -> "reduc") and stopwords ("the", "of") are
    dropped, for both documents and queries. Build once at startup; searching is fast.
    """

    def __init__(self, corpus: Corpus) -> None:
        start = time.perf_counter()
        self._documents = list(corpus)
        self._stemmer = Stemmer.Stemmer("english")
        # Titles are dense with key terms, so they are indexed with the abstract
        texts = [f"{doc.title} {doc.text}" for doc in self._documents]
        self._index = bm25s.BM25()
        self._index.index(self._tokenize(texts), show_progress=False)
        logger.info(
            "BM25 index built: %d documents in %.0fms",
            len(self._documents),
            (time.perf_counter() - start) * 1000,
        )

    async def search(self, query: str, k: int = 3) -> list[Passage]:
        k = min(k, len(self._documents))
        tokens = self._tokenize([query])
        if k <= 0 or not tokens[0]:
            return []

        indices, scores = self._index.retrieve(tokens, k=k, show_progress=False)
        return [
            Passage(document=self._documents[int(i)], score=float(s))
            for i, s in zip(indices[0], scores[0], strict=True)
            # A score of 0 means no shared words: not evidence, so leave it out
            if s > 0
        ]

    def _tokenize(self, texts: list[str]) -> list[list[str]]:
        # With return_ids=False, bm25s returns plain lists of tokens (its type hint also
        # allows its Tokenized object, used only when return_ids=True)
        tokens = bm25s.tokenize(
            texts,
            stopwords="en",
            stemmer=self._stemmer.stemWords,
            return_ids=False,
            show_progress=False,
        )
        return cast(list[list[str]], tokens)
