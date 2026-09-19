"""Ingests curated advisory documents (docs/<sector>/*.txt) into a Chroma collection.

Each document is chunked and stored with metadata: source, type, sector,
state, city, url_or_ref, file_path, chunk_index. STATE/CITY come straight
from the document header (see rag.metadata) - this module never guesses a
value for a document that omits one; it flags it instead (see
`needs_review` in IngestReport).
"""

import os
from dataclasses import dataclass, field

from rag.metadata import DocumentFormatError, parse_document

DEFAULT_COLLECTION_NAME = "nimit_docs"
DEFAULT_CHUNK_MAX_CHARS = 800


def chunk_text(body: str, max_chars: int = DEFAULT_CHUNK_MAX_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def iter_doc_files(docs_dir: str):
    for sector in sorted(os.listdir(docs_dir)):
        sector_dir = os.path.join(docs_dir, sector)
        if not os.path.isdir(sector_dir):
            continue
        for filename in sorted(os.listdir(sector_dir)):
            if filename.endswith(".txt"):
                yield os.path.join(sector_dir, filename)


@dataclass
class IngestReport:
    ingested_files: list[str] = field(default_factory=list)
    chunk_count: int = 0
    needs_review: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_collection(docs_dir: str, client, embedding_function=None, collection_name: str = DEFAULT_COLLECTION_NAME):
    """Parses every document under docs_dir and upserts its chunks into a Chroma collection.

    Returns (collection, IngestReport). Documents that fail to parse are
    skipped and recorded in report.errors; documents missing STATE/CITY are
    still ingested (tagged UNSPECIFIED, which matches no location filter) but
    recorded in report.needs_review so a human can fix them.
    """
    kwargs = {"name": collection_name}
    if embedding_function is not None:
        kwargs["embedding_function"] = embedding_function
    collection = client.get_or_create_collection(**kwargs)

    report = IngestReport()

    ids, documents, metadatas = [], [], []

    for file_path in iter_doc_files(docs_dir):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        try:
            doc = parse_document(text, file_path=file_path)
        except DocumentFormatError as e:
            report.errors.append(str(e))
            continue

        if doc.needs_review:
            report.needs_review.append(file_path)

        chunks = chunk_text(doc.body)
        for i, chunk in enumerate(chunks):
            ids.append(f"{file_path}::chunk{i}")
            documents.append(chunk)
            metadatas.append({
                "SOURCE": doc.source,
                "TYPE": doc.type,
                "SECTOR": doc.sector,
                "STATE": doc.state,
                "CITY": doc.city,
                "URL_OR_REF": doc.url_or_ref,
                "file_path": doc.file_path,
                "source_file": doc.file_path,
                "chunk_index": i,
            })

        report.ingested_files.append(file_path)
        report.chunk_count += len(chunks)

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    return collection, report


def main():
    import chromadb

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    collection, report = build_collection(docs_dir, client)

    print(f"Ingested {len(report.ingested_files)} document(s), {report.chunk_count} chunk(s).")
    if report.needs_review:
        print("\nNEEDS MANUAL REVIEW (missing STATE or CITY - flagged, not guessed):")
        for path in report.needs_review:
            print(f"  - {path}")
    if report.errors:
        print("\nERRORS (failed to parse, skipped):")
        for err in report.errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
