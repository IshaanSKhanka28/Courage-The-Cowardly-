import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.orchestrator import answer_query
from rules.heat_risk import evaluate_outdoor_activity_risk
from rules.rain_risk import evaluate_waterlogging_risk
from synthesis.synthesize import synthesize_answer

load_dotenv()

logger = logging.getLogger(__name__)

# ==========================================
# 1. LOCATION MAPPING & COORDINATES
# ==========================================

LOCATION_INFO: Dict[str, Dict[str, Any]] = {
    "mumbai": {
        "city": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.0760,
        "lon": 72.8777,
        "fallback": {
            "location": "Mumbai",
            "total_precipitation_mm": 42.0,
            "max_temperature_c": 31.2,
            "avg_relative_humidity": 85.0,
        },
    },
    "pune": {
        "city": "Pune",
        "state": "Maharashtra",
        "lat": 18.5204,
        "lon": 73.8567,
        "fallback": {
            "location": "Pune",
            "total_precipitation_mm": 25.0,
            "max_temperature_c": 29.5,
            "avg_relative_humidity": 78.0,
        },
    },
    "bengaluru": {
        "city": "Bengaluru",
        "state": "Karnataka",
        "lat": 12.9716,
        "lon": 77.5946,
        "fallback": {
            "location": "Bengaluru",
            "total_precipitation_mm": 30.0,
            "max_temperature_c": 27.0,
            "avg_relative_humidity": 75.0,
        },
    },
    "delhi": {
        "city": "Delhi",
        "state": "Delhi",
        "lat": 28.6139,
        "lon": 77.2090,
        "fallback": {
            "location": "Delhi",
            "total_precipitation_mm": 2.1,
            "max_temperature_c": 41.5,
            "avg_relative_humidity": 45.0,
        },
    },
    "ludhiana": {
        "city": "Ludhiana",
        "state": "Punjab",
        "lat": 30.9010,
        "lon": 75.8573,
        "fallback": {
            "location": "Ludhiana",
            "total_precipitation_mm": 5.0,
            "max_temperature_c": 38.0,
            "avg_relative_humidity": 50.0,
        },
    },
    "amritsar": {
        "city": "Amritsar",
        "state": "Punjab",
        "lat": 31.6340,
        "lon": 74.8723,
        "fallback": {
            "location": "Amritsar",
            "total_precipitation_mm": 6.0,
            "max_temperature_c": 37.5,
            "avg_relative_humidity": 52.0,
        },
    },
}

# ==========================================
# 2. CHROMA COLLECTION INITIALIZATION
# ==========================================

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "nimit_docs"

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_collection(COLLECTION_NAME)
except Exception as err:
    logger.warning("Chroma collection '%s' not loaded at startup: %s", COLLECTION_NAME, err)
    chroma_client = None
    chroma_collection = None


# ==========================================
# 3. SCHEMAS & API CONTRACT
# ==========================================

class Sector(str, Enum):
    TRAFFIC = "traffic"
    HEALTH = "health"
    AGRICULTURE = "agriculture"


class AskRequest(BaseModel):
    query: str = Field(
        ...,
        json_schema_extra={
            "example": "Will my commute via the Andheri Subway in Mumbai be flooded tomorrow morning?"
        },
    )
    location: str = Field(
        ...,
        json_schema_extra={"example": "Mumbai"},
    )
    sector: Optional[Sector] = Field(
        default=Sector.TRAFFIC,
        description="Sector context for retrieval and rule evaluation",
    )


class AskResponse(BaseModel):
    answer: str = Field(
        ...,
        description="Conversational, natural language response",
    )
    risk_level: str = Field(
        ...,
        description="LOW | MODERATE | HIGH | SEVERE",
        json_schema_extra={"example": "HIGH"},
    )
    reasoning_trace: List[str] = Field(
        ...,
        description="Deterministic step-by-step logic trace from Rule Engine",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Verified source URLs used in synthesis",
    )
    fallback_used: bool = Field(
        default=False,
        description="True if fallback weather data was used due to API failure",
    )


# ==========================================
# 4. HEURISTIC HELPERS
# ==========================================

FLOOD_PRONE_KEYWORDS = [
    "subway",
    "underpass",
    "low-lying",
    "andheri",
    "milan",
    "sion",
    "hindmata",
    "dadar",
    "kurla",
    "chembur",
    "thane",
    "khadki",
    "bopodi",
    "katraj",
    "kondhwa",
    "silk board",
    "bellandur",
    "ecospace",
    "panathur",
    "outer ring road",
    "orr",
    "marathahalli",
    "waterlog",
    "flood",
]

CHILDREN_KEYWORDS = [
    "kid",
    "kids",
    "child",
    "children",
    "son",
    "daughter",
    "school",
    "infant",
    "toddler",
    "baby",
]


def _detect_flood_zone(query: str) -> bool:
    q = query.lower()
    return any(keyword in q for keyword in FLOOD_PRONE_KEYWORDS)


def _detect_involves_children(query: str) -> bool:
    q = query.lower()
    return any(keyword in q for keyword in CHILDREN_KEYWORDS)


# ==========================================
# 5. OPEN-METEO WEATHER CLIENT
# ==========================================

async def get_weather_forecast(location: str) -> Tuple[Dict[str, Any], bool]:
    """Fetch real 1-day weather forecast from Open-Meteo, falling back to cached profile on error."""
    city_key = location.lower().strip()
    loc_info = LOCATION_INFO.get(city_key)

    if not loc_info:
        supported = ", ".join(sorted([info["city"] for info in LOCATION_INFO.values()]))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported location '{location}'. Supported locations: {supported}",
        )

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": loc_info["lat"],
        "longitude": loc_info["lon"],
        "hourly": "precipitation,temperature_2m,relative_humidity_2m",
        "forecast_days": 1,
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                hourly = data.get("hourly", {})
                precipitation = hourly.get("precipitation", [])
                temperatures = hourly.get("temperature_2m", [])
                humidity = hourly.get("relative_humidity_2m", [])

                total_rain = sum(value or 0 for value in precipitation)
                max_temp = (
                    max(temperatures)
                    if temperatures
                    else loc_info["fallback"]["max_temperature_c"]
                )
                avg_humidity = (
                    sum(value or 0 for value in humidity) / len(humidity)
                    if humidity
                    else loc_info["fallback"]["avg_relative_humidity"]
                )

                weather_data = {
                    "location": loc_info["city"],
                    "total_precipitation_mm": round(total_rain, 1),
                    "max_temperature_c": round(max_temp, 1),
                    "avg_relative_humidity": round(avg_humidity, 1),
                }
                return weather_data, False

            logger.warning("Open-Meteo returned HTTP %s for %s", response.status_code, location)
    except Exception as exc:
        logger.warning("Open-Meteo API call failed for %s: %s. Using fallback.", location, exc)

    return loc_info["fallback"], True


# ==========================================
# 6. FASTAPI APPLICATION & CORS
# ==========================================

app = FastAPI(
    title="Nimit Backend API",
    version="1.0.0",
    description="Backend API for weather risk assessment, evidence retrieval, and grounded synthesis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 7. HEALTH CHECK
# ==========================================

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Nimit Backend API",
        "version": "1.0.0",
    }


# ==========================================
# 8. ASK ENDPOINT
# ==========================================

@app.post("/ask", response_model=AskResponse)
async def ask_nimit(payload: AskRequest):
    # 1. Input validation
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query is required.")

    if not payload.location or not payload.location.strip():
        raise HTTPException(status_code=400, detail="Location is required.")

    city_key = payload.location.lower().strip()
    loc_info = LOCATION_INFO.get(city_key)

    if not loc_info:
        supported = ", ".join(sorted([info["city"] for info in LOCATION_INFO.values()]))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported location '{payload.location}'. Supported locations: {supported}",
        )

    # 2. Weather forecast
    weather_data, fallback_used = await get_weather_forecast(payload.location)

    # 3. Rule engine evaluation
    sector = payload.sector or Sector.TRAFFIC
    if sector == Sector.TRAFFIC:
        is_flood_zone = _detect_flood_zone(payload.query)
        rule_result = evaluate_waterlogging_risk(
            rainfall_mm=weather_data["total_precipitation_mm"],
            is_known_flood_zone=is_flood_zone,
        )
    elif sector == Sector.HEALTH:
        involves_children = _detect_involves_children(payload.query)
        rule_result = evaluate_outdoor_activity_risk(
            temp_c=weather_data["max_temperature_c"],
            humidity_pct=weather_data["avg_relative_humidity"],
            involves_children=involves_children,
        )
    else:
        # General / extensible fallback (e.g. agriculture)
        is_flood_zone = _detect_flood_zone(payload.query)
        rule_result = evaluate_waterlogging_risk(
            rainfall_mm=weather_data["total_precipitation_mm"],
            is_known_flood_zone=is_flood_zone,
        )

    # 4. Chroma collection resolution
    collection = chroma_collection
    if collection is None:
        try:
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            collection = client.get_collection(COLLECTION_NAME)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Chroma vector store: {exc}",
            )

    # 5. RAG Orchestration & Synthesis
    try:
        # If ANTHROPIC_API_KEY is present, use live Claude synthesis;
        # otherwise, provide a mock Anthropic client so local testing functions offline.
        if not os.environ.get("ANTHROPIC_API_KEY"):
            from tests.test_synthesize import FakeAnthropicClient
            import json as _json

            sources_cited = [e.get("source") for e in orchestrator_evidence if e.get("source")] if 'orchestrator_evidence' in locals() else []
            # Dynamically grounded fake response for offline / hackathon testing
            def offline_synthesizer(r_res, evid, q_text):
                srcs = [e.get("source") for e in evid if e.get("source")]
                primary_src = srcs[0] if srcs else "official guidelines"
                snippet = evid[0]["text"][:140].replace("\n", " ").strip() if evid else ""
                fake_text = (
                    f"Based on the {r_res.risk_level.value.upper()} risk assessment, please exercise caution. "
                    f"As noted by {primary_src}: \"{snippet}...\". "
                    f"Stay tuned to local advisories before traveling.\n\n"
                    f"```json\n"
                    f"{_json.dumps({'sources_cited': srcs[:2]})}\n"
                    f"```"
                )
                client_mock = FakeAnthropicClient(response_text=fake_text)
                try:
                    return synthesize_answer(r_res, evid, q_text, client=client_mock)
                except TypeError:
                    return synthesize_answer(r_res, evid, q_text)

            active_llm_fn = offline_synthesizer
        else:
            active_llm_fn = synthesize_answer

        orchestrator_result = answer_query(
            collection=collection,
            sector=sector.value,
            state=loc_info["state"],
            city=loc_info["city"],
            risk_result=rule_result,
            query_text=payload.query,
            llm_fn=active_llm_fn,
        )
    except Exception as exc:
        logger.error("Synthesis error in answer_query: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating grounded synthesis: {exc}",
        )

    return AskResponse(
        answer=orchestrator_result["answer"],
        risk_level=rule_result.risk_level.value.upper(),
        reasoning_trace=rule_result.reasoning,
        sources=orchestrator_result.get("sources", []),
        fallback_used=fallback_used,
    )


# ==========================================
# 9. LOCAL DEVELOPMENT ENTRY POINT
# ==========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ccc:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )