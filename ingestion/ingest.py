"""Ingestion pipeline for Nimit advisory documents.

Walks docs/<sector>/*.txt, parses metadata headers, chunks content, generates
embeddings via sentence-transformers/all-MiniLM-L6-v2, and stores each chunk
in a local Chroma collection (persisted under ./chroma_db/).

Metadata per chunk: SOURCE, TYPE, SECTOR, STATE, CITY, URL_OR_REF, chunk_index,
source_file. IDs are stable (hash of source_file + chunk_index).
"""

import hashlib
import os
import sys
from typing import Dict, List
from pathlib import Path

# Ensure project root is on the path so `rag.*` imports work regardless of CWD
sys.path.insert(0, str(Path(__file__).parent.parent))

from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

from rag.metadata import parse_document, DocumentFormatError, DocumentMetadata

# ── Configuration ──────────────────────────────────────────────────────────

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "nimit_docs"

CHUNK_MAX_WORDS = 250
CHUNK_OVERLAP_WORDS = 50

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ── Chunkering ─────────────────────────────────────────────────────────────

from ingestion.chunker import chunk_text


# ── Helpers ────────────────────────────────────────────────────────────────


def _chunk_id(source_file: str, chunk_index: int) -> str:
    """Stable ID per chunk: hash of source_file + chunk_index."""
    key = f"{source_file}::{chunk_index}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ── Main ingestion ─────────────────────────────────────────────────────────


def ingest_all(
    chroma_dir: Path = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME,
    chunk_max_words: int = CHUNK_MAX_WORDS,
    chunk_overlap_words: int = CHUNK_OVERLAP_WORDS,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> Dict[str, int]:
    """Walk docs directories, parse, chunk, embed, and store in Chroma.

    Returns a summary dict:
        {
            "documents_processed": int,
            "chunks_created": int,
            "by_sector": {"traffic": N, "health": N, "agriculture": N},
        }
    """
    # Ensure directories exist
    chroma_dir.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Load embedding model (local, no API key)
    model = SentenceTransformer(model_name)

    # Get or create Chroma collection; use stable IDs so re-running is idempotent
    client = PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name=collection_name,
        # We embed the chunk text; Chroma will store the vector.
    )

    # Track stats
    by_sector: Dict[str, int] = {}
    total_chunks = 0
    total_docs = 0
    skipped_docs: List[str] = []

    # Walk all .txt files under docs/<sector>/
    for sector_dir_path in sorted(DOCS_DIR.iterdir()):
        if not sector_dir_path.is_dir():
            continue
        sector_name = sector_dir_path.name  # e.g. "traffic", "health", "agriculture"

        # Ensure we track this sector even if all docs are skipped
        if sector_name not in by_sector:
            by_sector[sector_name] = 0

        for txt_file in sorted(sector_dir_path.iterdir()):
            if not txt_file.is_file() or not txt_file.name.endswith(".txt"):
                continue

            total_docs += 1

            try:
                raw = txt_file.read_text(encoding="utf-8")
            except Exception as e:
                skipped_docs.append(f"{txt_file}: read error: {e}")
                print(f"[WARN] Could not read {txt_file}: {e}")
                continue

            # Parse header + body
            try:
                doc: DocumentMetadata = parse_document(raw, file_path=str(txt_file))
            except DocumentFormatError as e:
                skipped_docs.append(f"{txt_file}: parse error: {e}")
                print(f"[WARN] Skip {txt_file}: {e}")
                continue

            # Enforce STATE and CITY presence — skip if missing (not guessed)
            if not doc.state:
                skipped_docs.append(
                    f"{txt_file}: missing STATE — skipping (not guessed)"
                )
                print(
                    f"[WARN] Skip {txt_file}: missing STATE field — "
                    "documents must declare STATE explicitly, not guessed."
                )
                continue
            if not doc.city:
                skipped_docs.append(
                    f"{txt_file}: missing CITY — skipping (not guessed)"
                )
                print(
                    f"[WARN] Skip {txt_file}: missing CITY field — "
                    "documents must declare CITY explicitly, not guessed."
                )
                continue

            # Chunk the body text
            chunks = chunk_text(doc.body, max_words=chunk_max_words,
                               overlap_words=chunk_overlap_words)

            if not chunks:
                print(f"[WARN] {txt_file}: body produced zero chunks — skipping")
                continue

            # Prepare Chroma upsert data
            ids: List[str] = []
            documents: List[str] = []
            metadatas: List[Dict[str, str]] = []

            for idx, chunk_text_body in enumerate(chunks):
                c_id = _chunk_id(str(txt_file), idx)

                meta: Dict[str, str] = {
                    "SOURCE": doc.source,
                    "TYPE": doc.type,
                    "SECTOR": doc.sector,
                    "STATE": doc.state,
                    "CITY": doc.city,
                    "URL_OR_REF": doc.url_or_ref,
                    "chunk_index": str(idx),
                    "source_file": str(txt_file),
                }

                ids.append(c_id)
                documents.append(chunk_text_body)
                metadatas.append(meta)

            # Upsert into Chroma (idempotent — same IDs overwrite)
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

            # Update stats
            n_chunks = len(chunks)
            total_chunks += n_chunks
            by_sector[sector_name] = by_sector.get(sector_name, 0) + n_chunks

            print(
                f"[OK] {txt_file}: {n_chunks} chunks "
                f"(SECTOR={doc.sector}, STATE={doc.state}, CITY={doc.city})"
            )

    # ── Summary ────────────────────────────────────────────────────────────
    summary = {
        "documents_processed": total_docs,
        "chunks_created": total_chunks,
        "by_sector": by_sector,
    }

    print("\n" + "=" * 50)
    print("INGESTION SUMMARY")
    print("=" * 50)
    print(f"Documents processed: {summary['documents_processed']}")
    print(f"Chunks created: {summary['chunks_created']}")
    for sector, count in summary["by_sector"].items():
        print(f"  {sector}: {count} chunks")
    if skipped_docs:
        print("\nSkipped documents:")
        for s in skipped_docs:
            print(f"  - {s}")
    print("=" * 50 + "\n")

    return summary


# ── CLI entry-point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    ingest_all()