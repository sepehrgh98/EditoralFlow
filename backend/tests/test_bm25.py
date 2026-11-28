"""BM25 search on the 5 fictional fixture abstracts."""

import pytest

from app.retrieval.base import Retriever
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.corpus import Corpus


@pytest.fixture
def retriever(corpus: Corpus) -> BM25Retriever:
    return BM25Retriever(corpus)


def test_is_a_retriever(retriever: BM25Retriever) -> None:
    assert isinstance(retriever, Retriever)


@pytest.mark.parametrize(
    ("query", "expected_doc_id"),
    [
        ("Statins lower cardiovascular mortality in heart disease", "101"),
        ("Vitamin D prevents hip fractures in older women", "102"),
        ("Aerobic exercise helps with depression", "103"),
        ("Malaria parasites resist artemisinin", "104"),
        ("Coffee in the evening delays sleep", "105"),
    ],
)
async def test_finds_the_matching_abstract_first(
    retriever: BM25Retriever, query: str, expected_doc_id: str
) -> None:
    results = await retriever.search(query)

    assert results[0].document.doc_id == expected_doc_id


async def test_different_word_forms_match(retriever: BM25Retriever) -> None:
    # "reduced" and "symptoms" vs the abstract's "reduces", "reduction"
    results = await retriever.search("exercise reduced depressive symptoms")

    assert results[0].document.doc_id == "103"


async def test_unrelated_query_finds_nothing(retriever: BM25Retriever) -> None:
    assert await retriever.search("quantum chromodynamics of gluons") == []


@pytest.mark.parametrize("query", ["", "   ", "the of and"])
async def test_empty_or_stopword_query_finds_nothing(retriever: BM25Retriever, query: str) -> None:
    assert await retriever.search(query) == []


async def test_k_limits_results_and_scores_are_sorted(retriever: BM25Retriever) -> None:
    # "patients" and "treatment" appear in several abstracts
    results = await retriever.search("patients treatment trial", k=2)

    assert len(results) <= 2
    scores = [p.score for p in results]
    assert scores == sorted(scores, reverse=True)
    assert all(score > 0 for score in scores)


async def test_k_larger_than_corpus_is_fine(retriever: BM25Retriever) -> None:
    results = await retriever.search("caffeine", k=50)

    assert 1 <= len(results) <= 5


async def test_k_zero_returns_nothing(retriever: BM25Retriever) -> None:
    assert await retriever.search("caffeine", k=0) == []
