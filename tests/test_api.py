import pytest
from fastapi.testclient import TestClient
import chromadb

import ccc
from ccc import app
from rules.thresholds import RiskLevel
from tests.fakes import FakeEmbeddingFunction
from tests.test_synthesize import FakeAnthropicClient


@pytest.fixture
def client_app(monkeypatch):
    # Setup test Chroma collection
    client = chromadb.EphemeralClient()
    coll = client.get_or_create_collection(
        name="test_api_collection",
        embedding_function=FakeEmbeddingFunction(),
    )
    coll.upsert(
        ids=["mumbai_traffic_1", "delhi_health_1"],
        documents=[
            "Andheri Subway closed due to heavy waterlogging in Mumbai.",
            "Delhi heat action plan guidelines for vulnerable children and schools.",
        ],
        metadatas=[
            {
                "SOURCE": "The Week",
                "TYPE": "news_secondary",
                "SECTOR": "traffic",
                "STATE": "Maharashtra",
                "CITY": "Mumbai",
                "URL_OR_REF": "https://www.theweek.in/mumbai-rains",
            },
            {
                "SOURCE": "Delhi DDMA",
                "TYPE": "government_guideline",
                "SECTOR": "health",
                "STATE": "Delhi",
                "CITY": "Delhi",
                "URL_OR_REF": "https://ddma.delhi.gov.in/heat-plan",
            },
        ],
    )

    # Monkeypatch the module-level chroma_collection
    monkeypatch.setattr(ccc, "chroma_collection", coll)

    # Monkeypatch synthesis to use FakeAnthropicClient
    fake_claude = FakeAnthropicClient(
        response_text=(
            "Given the high risk, avoid Andheri Subway as The Week reported closures.\n\n"
            '```json\n{"sources_cited": ["The Week"]}\n```'
        )
    )

    def fake_synthesize(rule_res, evidence, query_text, client=None, **kwargs):
        from synthesis.synthesize import synthesize_answer
        return synthesize_answer(rule_res, evidence, query_text, client=client or fake_claude)

    monkeypatch.setattr(ccc, "synthesize_answer", fake_synthesize)

    return TestClient(app)


def test_health_check_endpoint(client_app):
    response = client_app.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unsupported_location_returns_400(client_app):
    response = client_app.post(
        "/ask",
        json={
            "query": "Will it rain in Paris tomorrow?",
            "location": "Paris",
            "sector": "traffic",
        },
    )
    assert response.status_code == 400
    assert "Unsupported location 'Paris'" in response.json()["detail"]
    assert "Supported locations:" in response.json()["detail"]


def test_empty_query_returns_400(client_app):
    response = client_app.post(
        "/ask",
        json={
            "query": "   ",
            "location": "Mumbai",
            "sector": "traffic",
        },
    )
    assert response.status_code == 400
    assert "Query is required" in response.json()["detail"]


def test_traffic_query_uses_real_rule_engine_and_sources(client_app, monkeypatch):
    # Mock weather to return fixed 42mm rain (moderate base risk)
    async def mock_weather(location):
        return {
            "location": "Mumbai",
            "total_precipitation_mm": 42.0,
            "max_temperature_c": 31.0,
            "avg_relative_humidity": 85.0,
        }, False

    monkeypatch.setattr(ccc, "get_weather_forecast", mock_weather)

    response = client_app.post(
        "/ask",
        json={
            "query": "Will Andheri Subway be flooded tomorrow morning?",
            "location": "Mumbai",
            "sector": "traffic",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # (a) Real rule engine evaluation: 42mm -> moderate, Andheri subway -> escalated to HIGH
    assert data["risk_level"] == "HIGH"
    assert any("42.0mm of rainfall classifies as 'moderate'" in r for r in data["reasoning_trace"])
    assert any("escalating MODERATE -> HIGH" in r for r in data["reasoning_trace"])

    # (b) Sources must NOT be the old fake pair
    assert "BMC Drainage Report 2024" not in data["sources"]
    assert "IMD Mumbai Bulletin" not in data["sources"]
    assert "https://www.theweek.in/mumbai-rains" in data["sources"]


def test_health_query_evaluates_heat_risk(client_app, monkeypatch):
    # Mock weather for moderate heat in Delhi (33C, 50% humidity -> extreme_caution/MODERATE, escalates for children)
    async def mock_weather(location):
        return {
            "location": "Delhi",
            "total_precipitation_mm": 0.0,
            "max_temperature_c": 33.0,
            "avg_relative_humidity": 50.0,
        }, False

    monkeypatch.setattr(ccc, "get_weather_forecast", mock_weather)

    response = client_app.post(
        "/ask",
        json={
            "query": "Is it safe for children to play outside in the afternoon?",
            "location": "Delhi",
            "sector": "health",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Rule trace should show heat index and children escalation
    assert any("Heat index computed" in r for r in data["reasoning_trace"])
    assert any("Activity involves children" in r for r in data["reasoning_trace"])
