"""Retrieval layer for Nimit: filtered evidence extraction from Chroma vector store.

This module provides `retrieve_evidence` to fetch domain knowledge chunks
strictly scoped to sector and state (+ preferred city, with state-wide fallback).
It performs pure vector similarity search without LLM invocations.
"""

from typing import Any
import chromadb

DEFAULT_CHROMA_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "nimit_docs"
STATEWIDE_CITY_WILDCARDS = ["multiple", "state-wide", "ALL", "all"]


def _get_collection(
    collection=None,
    client=None,
    chroma_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """Resolves or connects to the Chroma collection.

    Raises RuntimeError if the collection cannot be reached or does not exist.
    """
    if collection is not None:
        return collection

    try:
        if client is None:
            client = chromadb.PersistentClient(path=chroma_path)
        existing_collections = [c.name for c in client.list_collections()]
        if collection_name not in existing_collections:
            raise RuntimeError(
                f"Collection '{collection_name}' not found at path '{chroma_path}'. "
                f"Available collections: {existing_collections}"
            )
        return client.get_collection(name=collection_name)
    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to Chroma collection '{collection_name}' at '{chroma_path}': {e}"
        ) from e


def _detect_key_casing(collection) -> dict[str, str]:
    """Inspects collection to detect whether metadata keys are uppercase or lowercase."""
    try:
        sample = collection.get(limit=1, include=["metadatas"])
        if sample and sample.get("metadatas") and sample["metadatas"]:
            first_meta = sample["metadatas"][0]
            if first_meta and "sector" in first_meta:
                return {
                    "SECTOR": "sector",
                    "STATE": "state",
                    "CITY": "city",
                    "SOURCE": "source",
                    "TYPE": "type",
                    "URL_OR_REF": "url_or_ref",
                }
    except Exception:
        pass

    return {
        "SECTOR": "SECTOR",
        "STATE": "STATE",
        "CITY": "CITY",
        "SOURCE": "SOURCE",
        "TYPE": "TYPE",
        "URL_OR_REF": "URL_OR_REF",
    }


def _get_meta_field(meta: dict | None, key: str) -> Any:
    if not meta:
        return None
    if key in meta:
        return meta[key]
    if key.upper() in meta:
        return meta[key.upper()]
    if key.lower() in meta:
        return meta[key.lower()]
    return None


def _format_query_results(raw_res: dict) -> list[dict]:
    """Transforms raw Chroma query output into standard dict format."""
    ids = raw_res.get("ids", [[]])[0]
    docs = raw_res.get("documents", [[]])[0]
    metas = raw_res.get("metadatas", [[]])[0]
    dists = raw_res.get("distances", [[]])[0] if "distances" in raw_res and raw_res["distances"] else []

    formatted = []
    for i in range(len(ids)):
        meta = metas[i] if i < len(metas) else {}
        doc = docs[i] if i < len(docs) else ""
        dist = dists[i] if i < len(dists) else None

        formatted.append({
            "id": ids[i],
            "text": doc,
            "source": _get_meta_field(meta, "SOURCE"),
            "type": _get_meta_field(meta, "TYPE"),
            "sector": _get_meta_field(meta, "SECTOR"),
            "state": _get_meta_field(meta, "STATE"),
            "city": _get_meta_field(meta, "CITY"),
            "url_or_ref": _get_meta_field(meta, "URL_OR_REF"),
            "distance": float(dist) if dist is not None else None,
        })
    return formatted


def retrieve_evidence(
    query_text: str,
    sector: str,
    state: str,
    city: str | None = None,
    top_k: int = 5,
    collection=None,
    client=None,
    chroma_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> list[dict]:
    """Retrieves relevant advisory chunks filtered strictly by sector and state.

    Args:
        query_text: The user query text for semantic similarity ranking.
        sector: Required sector filter (e.g. 'traffic', 'agriculture', 'health').
        state: Required state filter (e.g. 'Maharashtra', 'Karnataka', 'Punjab').
        city: Optional city filter (e.g. 'Mumbai', 'Bengaluru'). If provided,
            prefers chunks from that city, falling back to state-wide documents
            if fewer than `top_k` are found.
        top_k: Maximum number of evidence chunks to return.
        collection: Optional pre-loaded Chroma collection.
        client: Optional pre-configured Chroma client.
        chroma_path: Path to Chroma database if collection is not provided.
        collection_name: Collection name in Chroma database.

    Returns:
        List of dicts with keys: text, source, type, state, city, url_or_ref, distance.
        Returns an empty list [] if no curated documents exist for the sector+state.
    """
    coll = _get_collection(
        collection=collection,
        client=client,
        chroma_path=chroma_path,
        collection_name=collection_name,
    )

    if top_k <= 0:
        return []

    keys = _detect_key_casing(coll)
    sector_k = keys["SECTOR"]
    state_k = keys["STATE"]
    city_k = keys["CITY"]

    # 1. Existence check: Ensure exact sector + state combination exists in collection
    state_sector_filter = {
        "$and": [
            {sector_k: sector},
            {state_k: state},
        ]
    }

    try:
        check = coll.get(where=state_sector_filter, limit=1)
        if not check or not check.get("ids"):
            return []
    except Exception as e:
        raise RuntimeError(f"Error checking collection for state '{state}' and sector '{sector}': {e}") from e

    # 2. Case A: No specific city requested -> query all chunks in sector + state
    if not city:
        raw_res = coll.query(
            query_texts=[query_text],
            where=state_sector_filter,
            n_results=top_k,
        )
        return _format_query_results(raw_res)

    # 3. Case B: Specific city requested -> prefer city-specific chunks, fall back to state-wide
    city_filter = {
        "$and": [
            {sector_k: sector},
            {state_k: state},
            {city_k: city},
        ]
    }

    city_raw = coll.query(
        query_texts=[query_text],
        where=city_filter,
        n_results=top_k,
    )
    city_results = _format_query_results(city_raw)

    # If we already have enough city-specific chunks, return them
    if len(city_results) >= top_k:
        return city_results[:top_k]

    # Otherwise, query state-wide / wildcard chunks to supplement
    needed = top_k - len(city_results)
    fallback_filter = {
        "$and": [
            {sector_k: sector},
            {state_k: state},
            {city_k: {"$in": STATEWIDE_CITY_WILDCARDS}},
        ]
    }

    fallback_raw = coll.query(
        query_texts=[query_text],
        where=fallback_filter,
        n_results=needed,
    )
    fallback_results = _format_query_results(fallback_raw)

    # Combine city results first, then state-wide fallback
    seen_ids = set()
    combined = []

    for item in city_results:
        chunk_id = item["id"]
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            combined.append(item)

    for item in fallback_results:
        chunk_id = item["id"]
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            combined.append(item)
        if len(combined) >= top_k:
            break

    return combined
