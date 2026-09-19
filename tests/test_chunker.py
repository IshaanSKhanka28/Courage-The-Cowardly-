"""Pure-text chunker tests — no Chroma, no embedding model needed.

Tests the word-count-based splitter in ingestion/chunker.py.
"""

import pytest

from ingestion.chunker import chunk_text


class TestChunkText:
    def test_short_body_single_chunk(self):
        body = "This is a short body with only a few words."
        chunks = chunk_text(body, max_words=250, overlap_words=50)
        assert len(chunks) == 1
        assert chunks[0] == body

    def test_body_fits_within_max_words(self):
        body = " ".join(["word"] * 100)
        chunks = chunk_text(body, max_words=250, overlap_words=50)
        assert len(chunks) == 1

    def test_body_exceeds_max_words_splits_into_multiple(self):
        # 600 words → should split into at least 3 chunks (250 + 250 + 100)
        body = " ".join(["word"] * 600)
        chunks = chunk_text(body, max_words=250, overlap_words=50)
        assert len(chunks) >= 3
        # Each chunk should be near 250 words (allow small variance at ends)
        for c in chunks:
            wc = len(c.split())
            assert 50 <= wc <= 300, f"Chunk word count {wc} out of expected range"

    def test_overlap_preserved_between_chunks(self):
        # Build a body long enough for multiple chunks with overlap
        body = " ".join([f"w{i}" for i in range(500)])
        chunks = chunk_text(body, max_words=100, overlap_words=20)

        assert len(chunks) > 1, "Expected multiple chunks"

        # Verify overlap: last N words of chunk i should appear at start of chunk i+1
        for i in range(len(chunks) - 1):
            prev_words = set(chunks[i].split())
            next_words = set(chunks[i + 1].split())
            # The overlap should be at least overlap_words long
            overlap = prev_words.intersection(next_words)
            assert len(overlap) >= 20, (
                f"Chunk {i}→{i+1} overlap too small: {len(overlap)} words, "
                f"expected ≥20"
            )

    def test_empty_body_returns_empty_list(self):
        assert chunk_text("", max_words=250, overlap_words=50) == []

    def test_whitespace_body_returns_empty_list(self):
        assert chunk_text("   \n\n  ", max_words=250, overlap_words=50) == []

    def test_overlap_zero_still_splits(self):
        body = " ".join([f"w{i}" for i in range(250)] + [f"w{i}" for i in range(250, 500)])
        chunks = chunk_text(body, max_words=250, overlap_words=0)
        assert len(chunks) >= 2

    def test_overlap_more_than_body(self):
        # Body shorter than max_words + overlap should yield one chunk
        body = " ".join(["word"] * 50)
        chunks = chunk_text(body, max_words=250, overlap_words=500)
        assert len(chunks) == 1