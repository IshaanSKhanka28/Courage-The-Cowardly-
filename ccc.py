import logging
import os
import time
from datetime import datetime
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
from rules.crop_risk import evaluate_crop_risk
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


class HourlyForecastEntry(BaseModel):
    time: str = Field(..., description="'Now' or a formatted hour label, e.g. '3 PM'")
    temp_c: Optional[float] = None
    icon: str = Field(..., description="sun | cloud | rain | thunder")
    precip_probability: Optional[float] = Field(
        default=None, description="Percent chance of precipitation for this hour"
    )
    humidity_pct: Optional[float] = None
    wind_kmh: Optional[float] = None
    uv_index: Optional[float] = None
    is_day: bool = True


class RiskSummary(BaseModel):
    risk_level: str = Field(..., description="LOW | MODERATE | HIGH | SEVERE")
    reasoning: List[str]


class WeatherSnapshotResponse(BaseModel):
    location: str
    state: str
    condition: str = Field(..., description="Human-readable condition label derived from live data")
    icon: str = Field(..., description="sun | cloud | rain | thunder")
    is_day: bool = True
    temp_c: float
    wind_kmh: Optional[float] = None
    humidity_pct: float
    uv_index: Optional[float] = None
    visibility_km: Optional[float] = None
    pressure_hpa: Optional[float] = None
    sunrise: Optional[str] = Field(default=None, description="e.g. '6:27 AM', None in fallback mode")
    sunset: Optional[str] = Field(default=None, description="e.g. '6:36 PM', None in fallback mode")
    hourly: List[HourlyForecastEntry] = Field(default_factory=list)
    traffic_risk: RiskSummary
    health_risk: RiskSummary
    fallback_used: bool = Field(
        default=False,
        description="True if live Open-Meteo data was unavailable and a cached profile was used",
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

_OPEN_METEO_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_OPEN_METEO_CACHE_TTL_SECONDS = 600  # 10 minutes


async def _fetch_open_meteo(url: str, params: Dict[str, Any], timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """GET url with params, with a short TTL cache in front of it.

    Confirmed via Railway deploy logs: "Open-Meteo returned HTTP 429" on
    essentially every call, even spaced out ones - Open-Meteo's free tier
    rate-limits per source IP, and on a shared-egress-IP host like Railway
    that limit can be exhausted by *other* apps sharing the IP, not just this
    one's own traffic. Caching identical requests for a few minutes both cuts
    our own call volume and means a transient 429 doesn't immediately
    degrade every city to the static fallback profile - a cached real
    response is served instead. Returns the parsed JSON body on success
    (cached or fresh), or None if the request failed / was rate-limited and
    nothing usable is cached yet.
    """
    cache_key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items(), key=lambda kv: kv[0]))
    now = time.monotonic()

    cached = _OPEN_METEO_CACHE.get(cache_key)
    if cached is not None and (now - cached[0]) < _OPEN_METEO_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                _OPEN_METEO_CACHE[cache_key] = (now, data)
                return data
            logger.warning("Open-Meteo returned HTTP %s for params %s", response.status_code, params)
    except Exception as exc:
        logger.warning("Open-Meteo call failed for params %s: %s", params, exc)

    # Nothing fresh - serve a stale cache entry if we have one rather than
    # nothing, since "a few minutes old" beats "always the static fallback".
    if cached is not None:
        logger.warning("Serving stale (>%ss old) cached Open-Meteo response after failure.", _OPEN_METEO_CACHE_TTL_SECONDS)
        return cached[1]
    return None


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

    data = await _fetch_open_meteo(url, params)
    if data is not None:
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

    return loc_info["fallback"], True


def _weathercode_to_condition(code: Optional[int]) -> Tuple[str, str]:
    """Maps a WMO weather code (from Open-Meteo) to (icon, human label).
    Icon values match the sun/cloud/rain/thunder types WeatherPage renders."""
    if code is None:
        return "cloud", "Unknown"
    if code == 0:
        return "sun", "Clear Sky"
    if code in (1, 2):
        return "cloud", "Partly Cloudy"
    if code == 3:
        return "cloud", "Overcast"
    if code in (45, 48):
        return "cloud", "Foggy"
    if code in (51, 53, 55, 56, 57):
        return "rain", "Drizzle"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "rain", "Rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "cloud", "Snow"
    if code in (95, 96, 99):
        return "thunder", "Thunderstorm"
    return "cloud", "Unknown"


def _format_hour_label(iso_time: str) -> str:
    """'2026-09-20T14:00' -> '2 PM'. Avoids platform-specific strftime flags
    (Linux %-I vs Windows %#I) by formatting manually."""
    try:
        dt = datetime.fromisoformat(iso_time)
    except ValueError:
        return iso_time
    hour12 = dt.hour % 12 or 12
    period = "AM" if dt.hour < 12 else "PM"
    return f"{hour12} {period}"


def _format_clock_time(iso_time: str) -> str:
    """'2026-09-20T06:27' -> '6:27 AM'."""
    try:
        dt = datetime.fromisoformat(iso_time)
    except ValueError:
        return iso_time
    hour12 = dt.hour % 12 or 12
    period = "AM" if dt.hour < 12 else "PM"
    return f"{hour12}:{dt.minute:02d} {period}"


async def get_weather_snapshot(location: str) -> Tuple[Dict[str, Any], bool]:
    """Fetches a full current-conditions + hourly snapshot from Open-Meteo for the
    /weather endpoint (current temp, wind, humidity, UV, visibility, pressure,
    condition, next hours). Deliberately separate from get_weather_forecast (used
    by /ask) so that already-tested flow is untouched by this.

    On failure, falls back to the same cached per-city profile /ask already uses
    for temp/humidity/precip - but does NOT fabricate wind/UV/visibility/pressure
    or an hourly forecast for fields we have no real cached value for. Those come
    back as None/empty and fallback_used=True, so the frontend can say so honestly
    instead of inventing numbers.
    """
    city_key = location.lower().strip()
    loc_info = LOCATION_INFO.get(city_key)

    if not loc_info:
        supported = ", ".join(sorted(info["city"] for info in LOCATION_INFO.values()))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported location '{location}'. Supported locations: {supported}",
        )

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": loc_info["lat"],
        "longitude": loc_info["lon"],
        "hourly": (
            "temperature_2m,relative_humidity_2m,precipitation,"
            "precipitation_probability,windspeed_10m,surface_pressure,"
            "visibility,uv_index,weathercode,is_day"
        ),
        "daily": "sunrise,sunset",
        "current_weather": "true",
        "forecast_days": 1,
        "timezone": "auto",
    }

    data = await _fetch_open_meteo(url, params)
    if data is not None:
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        precip = hourly.get("precipitation", [])
        precip_prob = hourly.get("precipitation_probability", [])
        wind = hourly.get("windspeed_10m", [])
        pressure = hourly.get("surface_pressure", [])
        visibility = hourly.get("visibility", [])
        uv = hourly.get("uv_index", [])
        codes = hourly.get("weathercode", [])
        is_day_series = hourly.get("is_day", [])

        current = data.get("current_weather", {})
        current_time = current.get("time", "")
        current_hour_key = current_time[:13] + ":00" if len(current_time) >= 13 else None
        now_idx = times.index(current_hour_key) if current_hour_key in times else 0

        current_code = current.get("weathercode")
        if current_code is None and now_idx < len(codes):
            current_code = codes[now_idx]
        icon, condition = _weathercode_to_condition(current_code)

        current_is_day = current.get("is_day")
        is_day_now = bool(current_is_day) if current_is_day is not None else (
            bool(is_day_series[now_idx]) if now_idx < len(is_day_series) else True
        )

        hourly_entries = []
        for i in range(now_idx, min(now_idx + 7, len(times))):
            h_icon, _ = _weathercode_to_condition(codes[i] if i < len(codes) else None)
            hourly_entries.append({
                "time": "Now" if i == now_idx else _format_hour_label(times[i]),
                "temp_c": round(temps[i], 1) if i < len(temps) and temps[i] is not None else None,
                "icon": h_icon,
                "precip_probability": precip_prob[i] if i < len(precip_prob) else None,
                "humidity_pct": round(humidity[i], 1) if i < len(humidity) and humidity[i] is not None else None,
                "wind_kmh": round(wind[i], 1) if i < len(wind) and wind[i] is not None else None,
                "uv_index": round(uv[i], 1) if i < len(uv) and uv[i] is not None else None,
                "is_day": bool(is_day_series[i]) if i < len(is_day_series) else True,
            })

        total_rain = sum(value or 0 for value in precip)
        max_temp = max(temps) if temps else loc_info["fallback"]["max_temperature_c"]
        avg_humidity = (
            sum(value or 0 for value in humidity) / len(humidity)
            if humidity
            else loc_info["fallback"]["avg_relative_humidity"]
        )

        daily = data.get("daily", {})
        sunrise_list = daily.get("sunrise", [])
        sunset_list = daily.get("sunset", [])

        snapshot = {
            "location": loc_info["city"],
            "state": loc_info["state"],
            "condition": condition,
            "icon": icon,
            "is_day": is_day_now,
            "temp_c": round(
                current.get("temperature", temps[now_idx] if now_idx < len(temps) else max_temp), 1
            ),
            "wind_kmh": round(current.get("windspeed", wind[now_idx] if now_idx < len(wind) else 0) or 0, 1),
            "humidity_pct": round(humidity[now_idx], 1) if now_idx < len(humidity) else round(avg_humidity, 1),
            "uv_index": round(uv[now_idx], 1) if now_idx < len(uv) and uv[now_idx] is not None else None,
            "visibility_km": (
                round(visibility[now_idx] / 1000, 1)
                if now_idx < len(visibility) and visibility[now_idx] is not None
                else None
            ),
            "pressure_hpa": round(pressure[now_idx], 1) if now_idx < len(pressure) and pressure[now_idx] is not None else None,
            "sunrise": _format_clock_time(sunrise_list[0]) if sunrise_list else None,
            "sunset": _format_clock_time(sunset_list[0]) if sunset_list else None,
            "hourly": hourly_entries,
            "total_precipitation_mm": round(total_rain, 1),
            "max_temperature_c": round(max_temp, 1),
            "avg_relative_humidity": round(avg_humidity, 1),
        }
        return snapshot, False

    fb = loc_info["fallback"]
    if fb["total_precipitation_mm"] > 20:
        fallback_icon, fallback_condition = "rain", "Rain (cached estimate)"
    elif fb["total_precipitation_mm"] > 0:
        fallback_icon, fallback_condition = "cloud", "Cloudy (cached estimate)"
    else:
        fallback_icon, fallback_condition = "sun", "Clear (cached estimate)"

    snapshot = {
        "location": fb["location"],
        "state": loc_info["state"],
        "condition": fallback_condition,
        "icon": fallback_icon,
        "is_day": True,
        "temp_c": fb["max_temperature_c"],
        "wind_kmh": None,
        "humidity_pct": fb["avg_relative_humidity"],
        "uv_index": None,
        "visibility_km": None,
        "pressure_hpa": None,
        "sunrise": None,
        "sunset": None,
        "hourly": [],
        "total_precipitation_mm": fb["total_precipitation_mm"],
        "max_temperature_c": fb["max_temperature_c"],
        "avg_relative_humidity": fb["avg_relative_humidity"],
    }
    return snapshot, True


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
# 7a. TEMP DIAGNOSTIC: raw Open-Meteo reachability check
# ==========================================
# Exists only to diagnose why the deployed backend's Open-Meteo calls are
# falling back on Railway without needing dashboard/log access - returns the
# actual exception type/message instead of swallowing it. Safe to delete once
# the underlying issue is understood and fixed.

@app.get("/debug/network-check")
async def debug_network_check():
    result: Dict[str, Any] = {"target": "https://api.open-meteo.com/v1/forecast"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": 19.076, "longitude": 72.8777, "current_weather": "true"},
            )
            result["success"] = True
            result["status_code"] = response.status_code
            result["body_preview"] = response.text[:200]
    except Exception as exc:
        result["success"] = False
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = str(exc)
        result["exception_repr"] = repr(exc)
    return result


# ==========================================
# 7b. WEATHER SNAPSHOT ENDPOINT
# ==========================================

@app.get("/weather", response_model=WeatherSnapshotResponse)
async def get_weather(location: str):
    """Live current-conditions + hourly snapshot for one of the project's cities,
    pulled from Open-Meteo, plus real traffic/health risk from the rule engine
    (generic defaults: no known flood zone, no children specified - this endpoint
    isn't query-specific like /ask, so it reports the baseline risk for the
    location's current weather)."""
    if not location or not location.strip():
        raise HTTPException(status_code=400, detail="Location is required.")

    snapshot, fallback_used = await get_weather_snapshot(location)

    traffic_rule = evaluate_waterlogging_risk(
        rainfall_mm=snapshot["total_precipitation_mm"],
        is_known_flood_zone=False,
    )
    health_rule = evaluate_outdoor_activity_risk(
        temp_c=snapshot["max_temperature_c"],
        humidity_pct=snapshot["avg_relative_humidity"],
        involves_children=False,
    )

    return WeatherSnapshotResponse(
        location=snapshot["location"],
        state=snapshot["state"],
        condition=snapshot["condition"],
        icon=snapshot["icon"],
        is_day=snapshot["is_day"],
        temp_c=snapshot["temp_c"],
        wind_kmh=snapshot["wind_kmh"],
        humidity_pct=snapshot["humidity_pct"],
        uv_index=snapshot["uv_index"],
        visibility_km=snapshot["visibility_km"],
        pressure_hpa=snapshot["pressure_hpa"],
        sunrise=snapshot["sunrise"],
        sunset=snapshot["sunset"],
        hourly=snapshot["hourly"],
        traffic_risk=RiskSummary(
            risk_level=traffic_rule.risk_level.value.upper(),
            reasoning=traffic_rule.reasoning,
        ),
        health_risk=RiskSummary(
            risk_level=health_rule.risk_level.value.upper(),
            reasoning=health_rule.reasoning,
        ),
        fallback_used=fallback_used,
    )


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
    elif sector == Sector.AGRICULTURE:
        # Agriculture is currently only supported for Punjab (Ludhiana, Amritsar)
        loc_info = LOCATION_INFO.get(payload.location.lower().strip())
        if not loc_info or loc_info["state"] != "Punjab":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported location '{payload.location}' for agriculture sector. "
                    "Agriculture coverage is currently limited to Punjab (Ludhiana, Amritsar)."
                ),
            )
        # Heuristic: is_unseasonal = True if query contains unseasonal markers
        query_lower = (payload.query or "").lower()
        is_unseasonal = any(
            word in query_lower
            for word in ("unseasonal", "unusual", "unexpected")
        )
        rule_result = evaluate_crop_risk(
            rainfall_mm=weather_data["total_precipitation_mm"],
            crop_stage="grain_filling",  # hackathon simplification; not a real crop-calendar lookup
            is_unseasonal=is_unseasonal,
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
                risk = r_res.risk_level.value.upper()
                query = q_text.lower()
                if "crop" in query or "wheat" in query or "harvest" in query:
                    opening = "There is some crop risk here, worth watching."
                    advice = "Keep field drainage clear and check the crop closely after the rain."
                elif "child" in query or "kid" in query or "sports" in query or "heat" in query:
                    opening = "I'd hold off on outdoor activity during the hottest part of the day."
                    advice = "An early-morning or evening slot is the better option if practice cannot move indoors."
                elif risk in {"HIGH", "SEVERE"}:
                    opening = "Yeah, I'd avoid that route for now."
                    advice = "Use an alternative route and allow extra time if you have to travel."
                else:
                    opening = "You can probably go ahead, but keep an eye on conditions."
                    advice = "Give yourself a little extra time and recheck the local update before leaving."

                values = r_res.raw_values
                if "crop" in query or "wheat" in query or "harvest" in query:
                    rainfall = values.get("rainfall_mm")
                    crop_stage = values.get("crop_stage", "grain-filling")
                    opening = "Some risk here, and it is worth watching closely."
                    explanation = (
                        f"You are looking at about {rainfall:g}mm of rain, and I am assuming the wheat is "
                        f"at the {crop_stage.replace('_', '-')} stage based on the regional calendar; "
                        "that is when unseasonal rain can lead to lodging and disease."
                    )
                    advice = (
                        "Clear the field drainage and check for lodging or leaf disease after the rain."
                    )
                    closing = "One caveat: if your crop is at a different stage, the risk could be different."
                elif "child" in query or "kid" in query or "sports" in query or "heat" in query:
                    temperature = values.get("temp_c")
                    heat_index = values.get("heat_index_c")
                    opening = "I'd hold off, at least during the standard afternoon slot."
                    explanation = (
                        f"It is around {temperature:g}C, but the heat index feels closer to {heat_index:.1f}C, "
                        "which is a poor combination for children's outdoor exertion and heat illness risk."
                    )
                    advice = "Move practice indoors, or use an early-morning or evening slot if that is flexible."
                    closing = "I'd treat that as a high-confidence call because the heat reading and the guidance point the same way."
                else:
                    rainfall = values.get("rainfall_mm")
                    if values.get("is_known_flood_zone"):
                        opening = "Yeah, I'd avoid it if you can."
                        explanation = (
                            f"Mumbai is expecting around {rainfall:g}mm of rain, and the route is a known "
                            "flood-prone spot when rainfall gets into this range."
                        )
                        advice = "Take the flyover or push the commute past the heaviest rain if you can."
                        closing = "I'd call this a high-confidence call because the forecast and the area's track record point the same way."
                    else:
                        opening = "You can probably go ahead, but leave yourself some room."
                        explanation = f"The forecast is for around {rainfall:g}mm of rain in the area."
                        closing = "The exact conditions on your route may still vary."

                sources_json = _json.dumps({"sources_cited": srcs[:2]})
                fake_text = (
                    f"{opening} {explanation} {advice} {closing} "
                    f"That is consistent with the evidence from {primary_src}.\n\n"
                    f"```json\n{sources_json}\n```"
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

    port = int(os.environ.get("PORT", 8000))
    print(f"[startup] Resolved port: {port}", flush=True)
    print(f"[startup] GEMINI_API_KEY present: {bool(os.environ.get('GEMINI_API_KEY'))}", flush=True)
    print(f"[startup] ANTHROPIC_API_KEY present: {bool(os.environ.get('ANTHROPIC_API_KEY'))}", flush=True)
    uvicorn.run(
        "ccc:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
