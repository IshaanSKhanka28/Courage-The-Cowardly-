"""Pure-text chunker for advisory documents.

Splits document body into overlapping word-based chunks (~200-300 words
with ~50 word overlap between consecutive chunks). No external dependencies
beyond stdlib.
"""


def chunk_text(body: str, max_words: int = 250, overlap_words: int = 50) -> list[str]:
    """Chunk *body* into passages of roughly *max_words* each.

    Adjacent chunks overlap by *overlap_words* so context is preserved at
    boundaries. Returns a list of chunk strings (cleaned of leading/trailing
    whitespace, but otherwise unchanged).
    """
    if not body or not body.strip():
        return []

    words = body.split()
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap_words
        if start <= len(chunks) and start < 0:
            start = 0  # shouldn't happen, but safety

    return chunks