"""Corpus loading and the download script's extraction, without any network access."""

import io
import json
import tarfile
from pathlib import Path

import pytest

from app.retrieval.corpus import Corpus, CorpusError, Document, load_corpus
from scripts.download_scifact import WANTED, extract


def test_loads_every_document(corpus: Corpus) -> None:
    assert len(corpus) == 5
    assert [doc.doc_id for doc in corpus] == ["101", "102", "103", "104", "105"]


def test_lookup_by_id(corpus: Corpus) -> None:
    doc = corpus.get("102")

    assert doc is not None
    assert doc.title.startswith("Vitamin D supplementation")
    assert doc.sentences[2] == (
        "Vitamin D supplementation did not reduce the rate of hip or wrist fractures."
    )
    assert corpus.get("999") is None


def test_document_text_joins_sentences() -> None:
    doc = Document(doc_id="1", title="T", sentences=["One.", "Two."])

    assert doc.text == "One. Two."


def test_numeric_ids_become_strings(tmp_path: Path) -> None:
    path = tmp_path / "corpus.jsonl"
    path.write_text(json.dumps({"doc_id": 7, "title": " T ", "abstract": [" A. "]}) + "\n\n")

    doc = next(iter(load_corpus(path)))

    assert (doc.doc_id, doc.title, doc.sentences) == ("7", "T", ["A."])


def test_missing_file_says_how_to_fix_it(tmp_path: Path) -> None:
    with pytest.raises(CorpusError, match="make data"):
        load_corpus(tmp_path / "nope.jsonl")


def test_broken_line_is_reported_with_its_number(tmp_path: Path) -> None:
    path = tmp_path / "corpus.jsonl"
    good = json.dumps({"doc_id": 1, "title": "T", "abstract": ["A."]})
    path.write_text(f"{good}\n{{not json\n")

    with pytest.raises(CorpusError, match="line 2"):
        load_corpus(path)


def test_empty_file_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "corpus.jsonl"
    path.write_text("\n")

    with pytest.raises(CorpusError, match="empty"):
        load_corpus(path)


def test_duplicate_ids_are_an_error() -> None:
    doc = Document(doc_id="1", title="T", sentences=["A."])

    with pytest.raises(CorpusError, match="duplicate"):
        Corpus([doc, doc])


def make_archive(path: Path, files: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))


def test_extract_keeps_only_the_wanted_files(tmp_path: Path) -> None:
    archive = tmp_path / "data.tar.gz"
    files = {f"data/{name}": name.encode() for name in WANTED}
    files["data/README.md"] = b"not wanted"
    files["../outside.txt"] = b"must never be written"
    make_archive(archive, files)
    dest = tmp_path / "out"

    written = extract(archive, dest)

    assert sorted(p.name for p in written) == sorted(WANTED)
    assert sorted(p.name for p in dest.iterdir()) == sorted(WANTED)
    assert (dest / "corpus.jsonl").read_bytes() == b"corpus.jsonl"
    assert not (tmp_path / "outside.txt").exists()


def test_extract_fails_clearly_if_a_file_is_missing(tmp_path: Path) -> None:
    archive = tmp_path / "data.tar.gz"
    make_archive(archive, {"data/corpus.jsonl": b"x"})

    with pytest.raises(RuntimeError, match="claims_train.jsonl is missing"):
        extract(archive, tmp_path / "out")
