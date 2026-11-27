"""Shared test helpers."""

from pathlib import Path

import pytest

from app.retrieval.corpus import Corpus, load_corpus

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_CORPUS_PATH = FIXTURES / "scifact_corpus.jsonl"


@pytest.fixture
def corpus() -> Corpus:
    """The tiny fictional corpus: 5 abstracts, never the real download."""
    return load_corpus(FIXTURE_CORPUS_PATH)
