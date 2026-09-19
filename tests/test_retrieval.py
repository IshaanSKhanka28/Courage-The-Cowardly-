import chromadb
import pytest

from rag.retrieval import retrieve
from tests.fakes import FakeEmbeddingFunction


@pytest.fixture
def collection():
    client = chromadb.EphemeralClient()
    coll = client.get_or_create_collection(
        name="test_retrieval_scoping", embedding_function=FakeEmbeddingFunction()
    )
    coll.upsert(
        ids=["mumbai_1", "bengaluru_1", "national_rain_std", "delhi_health_1"],
        documents=[
            "Andheri subway waterlogging advisory for Mumbai commuters.",
            "MG Road waterlogging advisory for Bengaluru commuters.",
            "IMD national 24-hour rainfall intensity classification standard.",
            "Delhi heat wave advisory for vulnerable groups including children.",
        ],
        metadatas=[
            {"SECTOR": "traffic", "STATE": "Maharashtra", "CITY": "Mumbai",
             "SOURCE": "Mumbai Police", "TYPE": "news_secondary", "URL_OR_REF": "u1", "source_file": "f1"},
            {"SECTOR": "traffic", "STATE": "Karnataka", "CITY": "Bengaluru",
             "SOURCE": "BTP", "TYPE": "news_secondary", "URL_OR_REF": "u2", "source_file": "f2"},
            {"SECTOR": "traffic", "STATE": "National", "CITY": "ALL",
             "SOURCE": "IMD", "TYPE": "official_advisory", "URL_OR_REF": "u3", "source_file": "f3"},
            {"SECTOR": "health", "STATE": "Delhi", "CITY": "Delhi",
             "SOURCE": "DDMA", "TYPE": "government_guideline", "URL_OR_REF": "u4", "source_file": "f4"},
        ],
    )
    return coll


class TestRetrieveScoping:
    def test_mumbai_query_excludes_bengaluru_only_docs(self, collection):
        results = retrieve(
            collection, sector="traffic", state="Maharashtra", city="Mumbai",
            query_text="waterlogging near me",
        )
        ids = {r["id"] for r in results}
        assert "mumbai_1" in ids
        assert "bengaluru_1" not in ids

        # Explicitly assert that metadata fields are populated and not None
        mumbai_doc = next(r for r in results if r["id"] == "mumbai_1")
        assert mumbai_doc["source"] == "Mumbai Police"
        assert mumbai_doc["type"] == "news_secondary"
        assert mumbai_doc["state"] == "Maharashtra"
        assert mumbai_doc["city"] == "Mumbai"
        assert mumbai_doc["url_or_ref"] == "u1"
        assert mumbai_doc["sector"] == "traffic"

    def test_bengaluru_query_excludes_mumbai_only_docs(self, collection):
        results = retrieve(
            collection, sector="traffic", state="Karnataka", city="Bengaluru",
            query_text="waterlogging near me",
        )
        ids = {r["id"] for r in results}
        assert "bengaluru_1" in ids
        assert "mumbai_1" not in ids

    def test_national_scope_document_matches_every_state(self, collection):
        for state, city in [("Maharashtra", "Mumbai"), ("Karnataka", "Bengaluru")]:
            results = retrieve(
                collection, sector="traffic", state=state, city=city,
                query_text="rainfall classification",
            )
            ids = {r["id"] for r in results}
            assert "national_rain_std" in ids

    def test_sector_filter_is_respected(self, collection):
        results = retrieve(
            collection, sector="health", state="Maharashtra", city="Mumbai",
            query_text="anything",
        )
        ids = {r["id"] for r in results}
        assert ids == set()

    def test_state_only_filter_without_city(self, collection):
        results = retrieve(collection, sector="traffic", state="Maharashtra", query_text="rain")
        ids = {r["id"] for r in results}
        assert "mumbai_1" in ids
        assert "national_rain_std" in ids
        assert "bengaluru_1" not in ids

    def test_zero_result_location_returns_empty_list(self, collection):
        results = retrieve(
            collection, sector="traffic", state="Punjab", city="Ludhiana",
            query_text="waterlogging",
        )
        assert results == []

    def test_zero_result_location_skips_similarity_search_entirely(self, collection, monkeypatch):
        def _fail_if_called(*args, **kwargs):
            raise AssertionError("collection.query() must not run when the location has no matches")

        monkeypatch.setattr(collection, "query", _fail_if_called)

        results = retrieve(
            collection, sector="traffic", state="Punjab", city="Ludhiana",
            query_text="waterlogging",
        )
        assert results == []
