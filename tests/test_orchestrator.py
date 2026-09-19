import os

import chromadb
import pytest

from rag.ingest import build_collection
from rag.orchestrator import NO_ADVISORY_FALLBACK_ANSWER, answer_query
from rules.rain_risk import evaluate_waterlogging_risk
from tests.fakes import FakeEmbeddingFunction

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")


def _fail_if_called(*args, **kwargs):
    raise AssertionError("llm_fn must not be called when retrieval found zero evidence")


class TestZeroEvidenceFallback:
    """Karnataka has curated traffic documents for Bengaluru, but not for
    Mysuru - so a Mysuru query must fall back even though its own state
    (Karnataka) has *some* traffic evidence elsewhere. This is a stronger
    version of the task's scenario: it's not just "no docs for this state
    at all", it's "docs exist for this state, but not for this city", and
    that must still trigger the honest fallback rather than answering with
    a Bengaluru-specific advisory dressed up as being about Mysuru."""

    def test_mysuru_traffic_query_returns_honest_fallback_without_calling_llm(self):
        client = chromadb.EphemeralClient()
        collection, report = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_orchestrator_fallback",
        )
        assert report.errors == []

        # Rule engine risk is always computable, independent of retrieval/location.
        risk_result = evaluate_waterlogging_risk(rainfall_mm=80.0, is_known_flood_zone=False)

        response = answer_query(
            collection,
            sector="traffic",
            state="Karnataka",
            city="Mysuru",
            risk_result=risk_result,
            query_text="Is it safe to drive right now?",
            llm_fn=_fail_if_called,
        )

        assert response == {
            "risk_level": risk_result.risk_level.value,
            "evidence": [],
            "answer": NO_ADVISORY_FALLBACK_ANSWER,
            "sources": [],
        }

    def test_zero_evidence_state_only_query_also_falls_back(self):
        client = chromadb.EphemeralClient()
        collection, _ = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_orchestrator_fallback_state_only",
        )
        risk_result = evaluate_waterlogging_risk(rainfall_mm=10.0, is_known_flood_zone=False)

        response = answer_query(
            collection,
            sector="traffic",
            state="Punjab",
            risk_result=risk_result,
            query_text="Any flooding advisories for Ludhiana?",
            llm_fn=_fail_if_called,
        )

        assert response["evidence"] == []
        assert response["sources"] == []
        assert response["answer"] == NO_ADVISORY_FALLBACK_ANSWER
        assert response["risk_level"] == risk_result.risk_level.value


class TestNonEmptyEvidencePath:
    def test_mumbai_traffic_query_calls_llm_with_retrieved_evidence(self):
        client = chromadb.EphemeralClient()
        collection, _ = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_orchestrator_mumbai_evidence",
        )
        risk_result = evaluate_waterlogging_risk(rainfall_mm=80.0, is_known_flood_zone=True)

        captured = {}

        def fake_llm(query_text, evidence):
            captured["query_text"] = query_text
            captured["evidence"] = evidence
            return "Andheri Subway has a history of closures in heavy rain; avoid it."

        response = answer_query(
            collection,
            sector="traffic",
            state="Maharashtra",
            city="Mumbai",
            risk_result=risk_result,
            query_text="Is Andheri subway flooded right now?",
            llm_fn=fake_llm,
        )

        assert response["evidence"], "expected non-empty evidence for Mumbai traffic"
        assert response["answer"] == "Andheri Subway has a history of closures in heavy rain; avoid it."
        assert response["sources"], "expected at least one source URL"
        assert captured["query_text"] == "Is Andheri subway flooded right now?"

    def test_bengaluru_traffic_query_calls_llm_with_retrieved_evidence(self):
        client = chromadb.EphemeralClient()
        collection, _ = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_orchestrator_bengaluru_evidence",
        )
        risk_result = evaluate_waterlogging_risk(rainfall_mm=80.0, is_known_flood_zone=False)

        def fake_llm(query_text, evidence):
            return f"Based on {len(evidence)} local Bengaluru advisories, exercise caution."

        response = answer_query(
            collection,
            sector="traffic",
            state="Karnataka",
            city="Bengaluru",
            risk_result=risk_result,
            query_text="Is it safe to drive near Silk Board right now?",
            llm_fn=fake_llm,
        )

        assert response["evidence"], "expected non-empty evidence for Bengaluru traffic"
        # Evidence may also include supplementary National-scope docs (e.g. the
        # IMD rainfall standard) - what matters is at least one Karnataka-specific hit.
        assert any(e["state"] == "Karnataka" for e in response["evidence"])
        assert response["sources"], "expected at least one source URL"

    def test_raises_if_llm_fn_missing_when_evidence_exists(self):
        client = chromadb.EphemeralClient()
        collection, _ = build_collection(
            DOCS_DIR, client, embedding_function=FakeEmbeddingFunction(),
            collection_name="test_orchestrator_missing_llm_fn",
        )
        risk_result = evaluate_waterlogging_risk(rainfall_mm=80.0, is_known_flood_zone=True)

        with pytest.raises(ValueError):
            answer_query(
                collection,
                sector="traffic",
                state="Maharashtra",
                city="Mumbai",
                risk_result=risk_result,
                query_text="Is Andheri subway flooded right now?",
            )
