import os

import chromadb

from rag.ingest import build_collection, chunk_text, iter_doc_files
from tests.fakes import FakeEmbeddingFunction

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")


class TestChunkText:
    def test_splits_on_paragraph_boundaries(self):
        body = "Para one.\n\nPara two.\n\nPara three."
        chunks = chunk_text(body, max_chars=1000)
        assert len(chunks) == 1
        assert "Para one." in chunks[0]
        assert "Para three." in chunks[0]

    def test_splits_when_exceeding_max_chars(self):
        body = "A" * 500 + "\n\n" + "B" * 500 + "\n\n" + "C" * 500
        chunks = chunk_text(body, max_chars=800)
        assert len(chunks) > 1
        assert all(len(c) <= 1000 for c in chunks)

    def test_empty_body_yields_no_chunks(self):
        assert chunk_text("   \n\n  ") == []


class TestBuildCollection:
    def test_ingests_real_docs_with_state_and_city_metadata(self):
        client = chromadb.EphemeralClient()
        collection, report = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_ingest_real_docs",
        )

        assert report.errors == []
        assert report.needs_review == []
        assert len(report.ingested_files) == len(list(iter_doc_files(DOCS_DIR)))
        assert report.chunk_count > 0

        sample = collection.get(where={"file_path": {"$ne": ""}}, limit=1)
        assert sample["metadatas"], "expected at least one ingested chunk"

        all_chunks = collection.get(limit=1000)
        states = {m["state"] for m in all_chunks["metadatas"]}
        cities = {m["city"] for m in all_chunks["metadatas"]}

        assert "Maharashtra" in states
        assert "Delhi" in states
        assert "National" in states
        assert "Mumbai" in cities
        assert "ALL" in cities

    def test_every_chunk_has_full_metadata(self):
        client = chromadb.EphemeralClient()
        collection, _ = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_ingest_metadata_shape",
        )
        all_chunks = collection.get(limit=1000)
        for metadata in all_chunks["metadatas"]:
            for key in ("source", "type", "sector", "state", "city", "url_or_ref", "file_path"):
                assert metadata.get(key), f"missing {key} in {metadata}"
