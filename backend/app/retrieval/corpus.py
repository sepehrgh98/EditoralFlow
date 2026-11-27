"""The source library: SciFact abstracts, each split into numbered sentences.

File format (one JSON object per line, as in the SciFact release):
    {"doc_id": 4983, "title": "...", "abstract": ["sentence 0", "sentence 1", ...], ...}

Sentence numbers are positions in `sentences`. The verifier cites by number and the code
looks the text up here, so a quote can never be invented (ADR 0008).
"""

import json
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel, ValidationError

# backend/data/scifact/corpus.jsonl, written by `make data`
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "scifact" / "corpus.jsonl"


class Document(BaseModel):
    """One source abstract."""

    doc_id: str
    title: str
    sentences: list[str]

    @property
    def text(self) -> str:
        """The whole abstract as one string (what search indexes)."""
        return " ".join(self.sentences)


class CorpusError(Exception):
    """The corpus file is missing or broken."""


class Corpus:
    """All documents, in file order, with lookup by id."""

    def __init__(self, documents: list[Document]) -> None:
        self._documents = documents
        self._by_id = {doc.doc_id: doc for doc in documents}
        if len(self._by_id) != len(documents):
            raise CorpusError("Corpus has duplicate doc_id values")

    def __len__(self) -> int:
        return len(self._documents)

    def __iter__(self) -> Iterator[Document]:
        return iter(self._documents)

    def get(self, doc_id: str) -> Document | None:
        return self._by_id.get(doc_id)


class _RawDocument(BaseModel):
    """One line of the SciFact file, before conversion."""

    doc_id: int | str
    title: str
    abstract: list[str]


def load_corpus(path: Path = DEFAULT_CORPUS_PATH) -> Corpus:
    """Read a SciFact-format corpus file."""
    if not path.is_file():
        raise CorpusError(f"Corpus not found at {path}: run `make data` to download it")

    documents: list[Document] = []
    with path.open(encoding="utf-8") as lines:
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                raw = _RawDocument.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise CorpusError(f"{path}, line {number}: not a valid document ({exc})") from exc
            sentences = [s.strip() for s in raw.abstract]
            documents.append(
                Document(doc_id=str(raw.doc_id), title=raw.title.strip(), sentences=sentences)
            )

    if not documents:
        raise CorpusError(f"Corpus at {path} is empty")
    return Corpus(documents)
