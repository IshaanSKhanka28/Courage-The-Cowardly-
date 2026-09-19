"""Filtered retrieval over the Chroma collection built by rag.ingest.

Filtering by sector + state (+ city) happens via Chroma's `where` clause
*before* any similarity search runs. A "National" STATE, or a CITY wildcard
("ALL", "state-wide", "multiple" - see rag.metadata.CITY_WILDCARDS) on a
document means it applies more broadly than one city, so it supplements a
query for any matching location - but it never counts, by itself, as
evidence that a *local* (city- or district-specific) advisory exists.

That distinction matters for the zero-result fallback: retrieve() first
checks for at least one document whose STATE exactly matches the requested
state (a real local advisory, e.g. Maharashtra/Mumbai). Only if that check
finds something does it broaden the query to also pull in National-scope
reference material as supplementary context. If no state-specific document
exists, retrieve() returns [] immediately - without running a similarity
search and without letting a nationwide standard masquerade as "we have a
local advisory for this place". Callers (see rag.orchestrator) use an empty
result to skip the LLM call entirely.
"""

from rag.metadata import CITY_WILDCARDS, NATIONAL_STATE

DEFAULT_N_RESULTS = 5


def _city_clause(city: str) -> dict:
    return {"city": {"$in": [city, *CITY_WILDCARDS]}}


def _build_local_where(sector: str, state: str, city: str | None) -> dict:
    """Strict filter: state must exactly match (no National fallback). Used
    only to check whether any *local* evidence exists for this location."""
    clauses = [
        {"sector": {"$eq": sector}},
        {"state": {"$eq": state}},
    ]
    if city:
        clauses.append(_city_clause(city))
    return {"$and": clauses}


def _build_where(sector: str, state: str, city: str | None) -> dict:
    clauses = [
        {"sector": {"$eq": sector}},
        {"$or": [{"state": {"$eq": state}}, {"state": {"$eq": NATIONAL_STATE}}]},
    ]
    if city:
        clauses.append(_city_clause(city))
    return {"$and": clauses}


def _format_metadatas_and_documents(ids, documents, metadatas) -> list[dict]:
    results = []
    for doc_id, document, metadata in zip(ids, documents, metadatas):
        results.append({
            "id": doc_id,
            "text": document,
            "source": metadata.get("source"),
            "type": metadata.get("type"),
            "sector": metadata.get("sector"),
            "state": metadata.get("state"),
            "city": metadata.get("city"),
            "url_or_ref": metadata.get("url_or_ref"),
            "file_path": metadata.get("file_path"),
        })
    return results


def retrieve(
    collection,
    sector: str,
    state: str,
    city: str | None = None,
    query_text: str | None = None,
    n_results: int = DEFAULT_N_RESULTS,
) -> list[dict]:
    """Returns up to n_results chunks matching sector+state(+city), ranked by
    similarity to query_text. Returns [] if no document with an exact STATE
    match exists for this location - without running any similarity search -
    even if a National-scope document would otherwise match."""

    local_where = _build_local_where(sector, state, city)
    local_existence_check = collection.get(where=local_where, limit=1)
    if not local_existence_check["ids"]:
        return []

    where = _build_where(sector, state, city)

    if query_text is None:
        result = collection.get(where=where, limit=n_results)
        return _format_metadatas_and_documents(
            result["ids"], result["documents"], result["metadatas"]
        )

    result = collection.query(query_texts=[query_text], where=where, n_results=n_results)
    return _format_metadatas_and_documents(
        result["ids"][0], result["documents"][0], result["metadatas"][0]
    )
