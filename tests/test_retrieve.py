import os
import chromadb
import pytest

from retrieval.retrieve import retrieve_evidence
from tests.fakes import FakeEmbeddingFunction


@pytest.fixture
def mock_collection():
    client = chromadb.EphemeralClient()
    coll = client.get_or_create_collection(
        name="test_retrieve_collection",
        embedding_function=FakeEmbeddingFunction(),
    )
    coll.upsert(
        ids=[
            "mumbai_traffic_1",
            "mumbai_traffic_2",
            "pune_traffic_1",
            "maharashtra_statewide_traffic_1",
            "bengaluru_traffic_1",
            "punjab_agri_ludhiana_1",
            "punjab_agri_statewide_1",
            "delhi_health_1",
        ],
        documents=[
            "Andheri subway closed due to heavy flooding in Mumbai.",
            "Milan subway waterlogging in Mumbai causes traffic jams.",
            "Katraj tunnel waterlogging in Pune traffic advisory.",
            "Maharashtra state disaster management authority traffic warning for entire state.",
            "Silk Board junction traffic waterlogging in Bengaluru.",
            "Ludhiana wheat crop advisory during heavy rain.",
            "Punjab state-wide agricultural advisory for unseasonal rainfall.",
            "Delhi heat wave advisory for schools and children.",
        ],
        metadatas=[
            {
                "SOURCE": "Mumbai Police",
                "TYPE": "official_advisory",
                "SECTOR": "traffic",
                "STATE": "Maharashtra",
                "CITY": "Mumbai",
                "URL_OR_REF": "https://mumbaipolice.gov.in/1",
            },
            {
                "SOURCE": "The Week",
                "TYPE": "news_secondary",
                "SECTOR": "traffic",
                "STATE": "Maharashtra",
                "CITY": "Mumbai",
                "URL_OR_REF": "https://theweek.in/mumbai-2",
            },
            {
                "SOURCE": "Pune Pulse",
                "TYPE": "news_secondary",
                "SECTOR": "traffic",
                "STATE": "Maharashtra",
                "CITY": "Pune",
                "URL_OR_REF": "https://punepulse.com/1",
            },
            {
                "SOURCE": "Maharashtra SDMA",
                "TYPE": "government_guideline",
                "SECTOR": "traffic",
                "STATE": "Maharashtra",
                "CITY": "state-wide",
                "URL_OR_REF": "https://maharashtra.gov.in/sdma",
            },
            {
                "SOURCE": "Bengaluru Traffic Police",
                "TYPE": "official_advisory",
                "SECTOR": "traffic",
                "STATE": "Karnataka",
                "CITY": "Bengaluru",
                "URL_OR_REF": "https://btp.gov.in/1",
            },
            {
                "SOURCE": "PAU Ludhiana",
                "TYPE": "government_guideline",
                "SECTOR": "agriculture",
                "STATE": "Punjab",
                "CITY": "Ludhiana",
                "URL_OR_REF": "https://pau.edu/1",
            },
            {
                "SOURCE": "ICAR Punjab",
                "TYPE": "government_guideline",
                "SECTOR": "agriculture",
                "STATE": "Punjab",
                "CITY": "multiple",
                "URL_OR_REF": "https://icar.gov.in/punjab",
            },
            {
                "SOURCE": "Delhi DDMA",
                "TYPE": "government_guideline",
                "SECTOR": "health",
                "STATE": "Delhi",
                "CITY": "Delhi",
                "URL_OR_REF": "https://ddma.delhi.gov.in/1",
            },
        ],
    )
    return coll


def test_known_sector_state_returns_matching_results(mock_collection):
    results = retrieve_evidence(
        query_text="flooding on main road",
        sector="traffic",
        state="Maharashtra",
        top_k=5,
        collection=mock_collection,
    )
    assert len(results) > 0
    for res in results:
        assert res["sector"] == "traffic"
        assert res["state"] == "Maharashtra"
        assert res["text"] is not None
        assert res["source"] is not None
        assert res["type"] is not None
        assert res["url_or_ref"] is not None
        assert "distance" in res


def test_unknown_state_returns_empty_list(mock_collection):
    results = retrieve_evidence(
        query_text="waterlogging and rain",
        sector="traffic",
        state="Goa",
        top_k=5,
        collection=mock_collection,
    )
    assert results == []


def test_unknown_sector_returns_empty_list(mock_collection):
    results = retrieve_evidence(
        query_text="heatstroke warning",
        sector="cybersecurity",
        state="Maharashtra",
        top_k=5,
        collection=mock_collection,
    )
    assert results == []


def test_city_filter_prefers_matching_city(mock_collection):
    results = retrieve_evidence(
        query_text="subway closure",
        sector="traffic",
        state="Maharashtra",
        city="Mumbai",
        top_k=2,
        collection=mock_collection,
    )
    assert len(results) == 2
    for res in results:
        assert res["city"] == "Mumbai"
        assert res["state"] == "Maharashtra"


def test_city_fallback_to_statewide(mock_collection):
    # Pune has 1 city-specific doc and 1 state-wide doc in mock collection
    results = retrieve_evidence(
        query_text="waterlogging emergency traffic",
        sector="traffic",
        state="Maharashtra",
        city="Pune",
        top_k=3,
        collection=mock_collection,
    )
    cities = [r["city"] for r in results]
    assert "Pune" in cities
    assert "state-wide" in cities
    # Bengaluru or other states must NEVER leak
    for res in results:
        assert res["state"] == "Maharashtra"
        assert res["sector"] == "traffic"


def test_unreachable_collection_raises_runtime_error():
    with pytest.raises(RuntimeError) as excinfo:
        retrieve_evidence(
            query_text="test",
            sector="traffic",
            state="Maharashtra",
            chroma_path="./non_existent_chroma_path_xyz",
            collection_name="non_existent_collection",
        )
    assert "Failed to connect to Chroma" in str(excinfo.value) or "not found" in str(excinfo.value)


@pytest.mark.skipif(not os.path.exists("./chroma_db"), reason="./chroma_db not found")
def test_live_chroma_db_mumbai_flooding():
    results = retrieve_evidence(
        query_text="will it flood in Andheri tomorrow",
        sector="traffic",
        state="Maharashtra",
        city="Mumbai",
        top_k=3,
        chroma_path="./chroma_db",
        collection_name="nimit_docs",
    )
    assert len(results) > 0
    for r in results:
        assert r["state"] == "Maharashtra"
        assert r["sector"] == "traffic"
        assert r["city"] in ["Mumbai", "state-wide", "multiple", "ALL"]
