"""Download the SciFact dataset once into backend/data/scifact/.

Run with `make data` (or: uv run python -m scripts.download_scifact [--force]).

Source: the official release by AllenAI, https://github.com/allenai/scifact
License: CC BY-NC 2.0 (non-commercial use).
"""

import argparse
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx

URL = "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "scifact"
# The only files we keep from the archive (their names inside it are data/<name>)
WANTED = ("corpus.jsonl", "claims_train.jsonl", "claims_dev.jsonl", "claims_test.jsonl")


def extract(archive: Path, dest: Path) -> list[Path]:
    """Copy the WANTED files out of the archive into dest. Ignores everything else.

    Members are read by exact name and written to paths we build ourselves, so a crafted
    archive cannot write outside dest.
    """
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with tarfile.open(archive, "r:gz") as tar:
        members = {member.name: member for member in tar.getmembers() if member.isfile()}
        for name in WANTED:
            member = members.get(f"data/{name}")
            if member is None:
                raise RuntimeError(f"{name} is missing from the SciFact archive")
            source = tar.extractfile(member)
            if source is None:
                raise RuntimeError(f"Could not read {name} from the archive")
            target = dest / name
            target.write_bytes(source.read())
            written.append(target)
    return written


def download(url: str, target: Path) -> None:
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with target.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="download again even if present")
    args = parser.parse_args(argv)

    corpus = DATA_DIR / "corpus.jsonl"
    if corpus.is_file() and not args.force:
        print(f"SciFact already present in {DATA_DIR} (use --force to download again)")
        return 0

    print(f"Downloading SciFact from {URL} ...")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "scifact.tar.gz"
        download(URL, archive)
        written = extract(archive, DATA_DIR)

    # Imported here so the script's own logic does not depend on the app package
    from app.retrieval.corpus import load_corpus

    documents = len(load_corpus(corpus))
    for path in written:
        print(f"  {path.relative_to(DATA_DIR.parent.parent)}")
    print(f"Done: {documents} abstracts in the corpus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
