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
            {"sector": "traffic", "state": "Maharashtra", "city": "Mumbai",
             "source": "s", "type": "news_secondary", "url_or_ref": "u1", "file_path": "f1"},
            {"sector": "traffic", "state": "Karnataka", "city": "Bengaluru",
             "source": "s", "type": "news_secondary", "url_or_ref": "u2", "file_path": "f2"},
            {"sector": "traffic", "state": "National", "city": "ALL",
             "source": "s", "type": "official_advisory", "url_or_ref": "u3", "file_path": "f3"},
            {"sector": "health", "state": "Delhi", "city": "Delhi",
             "source": "s", "type": "government_guideline", "url_or_ref": "u4", "file_path": "f4"},
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
