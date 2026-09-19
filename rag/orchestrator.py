"""Combines the (location-agnostic) rule engine output with retrieved local
evidence to produce a final response.

The rule engine (rules/) always returns a risk_level - it's deterministic and
needs no documents. Grounded natural-language advice, however, requires real
local evidence. If retrieval finds zero curated documents for the requested
sector+state(+city), the LLM is never called: there is nothing for it to be
grounded in, and calling it anyway would just invite improvisation dressed up
as a sourced answer. `answer_query` returns the honest fallback below instead.
"""

from rag.retrieval import DEFAULT_N_RESULTS, retrieve

NO_ADVISORY_FALLBACK_ANSWER = (
    "I can give you the risk level based on the forecast, but I don't have a "
    "verified local advisory on file for this area yet."
)


def answer_query(
    collection,
    sector: str,
    state: str,
    risk_result,
    query_text: str,
    city: str | None = None,
    n_results: int = DEFAULT_N_RESULTS,
    llm_fn=None,
) -> dict:
    """Returns {risk_level, evidence, answer, sources}.

    risk_result: a RuleResult from rules/rain_risk.py or rules/heat_risk.py
    (or anything exposing a `.risk_level` with a `.value`), computed by the
    caller before this function is invoked - it is not recomputed here since
    rules/ is location-agnostic and doesn't need retrieval to run.

    llm_fn: callable(query_text, evidence: list[dict]) -> str. Only invoked
    when evidence is non-empty; never called for a zero-evidence location.
    """
    evidence = retrieve(
        collection, sector, state, city=city, query_text=query_text, n_results=n_results
    )

    if not evidence:
        return {
            "risk_level": risk_result.risk_level.value,
            "evidence": [],
            "answer": NO_ADVISORY_FALLBACK_ANSWER,
            "sources": [],
        }

    if llm_fn is None:
        raise ValueError(
            "llm_fn is required once evidence was found - answer_query() will not "
            "silently skip the LLM call when there is real evidence to ground it in"
        )

    try:
        raw_output = llm_fn(query_text, evidence)
    except TypeError:
        raw_output = llm_fn(risk_result, evidence, query_text)

    if isinstance(raw_output, dict):
        answer = raw_output.get("answer", "")
        extracted_sources = raw_output.get("sources", [])
        if extracted_sources:
            if isinstance(extracted_sources[0], dict):
                sources = sorted({s.get("url_or_ref") or s.get("URL_OR_REF") for s in extracted_sources if s.get("url_or_ref") or s.get("URL_OR_REF")})
            else:
                sources = sorted(set(extracted_sources))
        else:
            sources = sorted({e["url_or_ref"] for e in evidence if e.get("url_or_ref")})
    else:
        answer = str(raw_output)
        sources = sorted({e["url_or_ref"] for e in evidence if e.get("url_or_ref")})

    return {
        "risk_level": risk_result.risk_level.value,
        "evidence": evidence,
        "answer": answer,
        "sources": sources,
    }
