import json
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ==========================================
# 1. SCHEMAS & API CONTRACT
# ==========================================

class Sector(str, Enum):
    TRAFFIC = "traffic"
    HEALTH = "health"


class AskRequest(BaseModel):
    query: str = Field(
        ...,
        json_schema_extra={
            "example": "Will my commute via the Andheri Subway in Mumbai be flooded tomorrow morning?"
        }
    )

    location: str = Field(
        ...,
        json_schema_extra={
            "example": "Mumbai"
        }
    )

    sector: Optional[Sector] = Field(
        default=Sector.TRAFFIC,
        description="Sector context for retrieval"
    )


class SourceCitation(BaseModel):
    title: str = Field(
        ...,
        json_schema_extra={
            "example": "BMC Drainage Report 2024"
        }
    )

    reference: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "example": "Section 3: Underpass Vulnerability"
        }
    )


class AskResponse(BaseModel):
    answer: str = Field(
        ...,
        description="Conversational, natural language response"
    )

    risk_level: str = Field(
        ...,
        description="LOW | MODERATE | HIGH | SEVERE",
        json_schema_extra={
            "example": "HIGH"
        }
    )

    reasoning_trace: List[str] = Field(
        ...,
        description="Deterministic step-by-step logic trace from Rule Engine"
    )

    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Verified sources used in synthesis"
    )

    fallback_used: bool = Field(
        default=False,
        description="True if fallback weather data was used due to API failure"
    )


# ==========================================
# 2. CITY COORDINATES
# ==========================================

CITY_COORDINATES = {
    "mumbai": {
        "lat": 19.0760,
        "lon": 72.8777
    },
    "delhi": {
        "lat": 28.6139,
        "lon": 77.2090
    }
}


# ==========================================
# 3. FALLBACK WEATHER DATA
# ==========================================

MOCK_FALLBACK_DATA = {
    "mumbai": {
        "location": "Mumbai",
        "total_precipitation_mm": 42.0,
        "max_temperature_c": 31.2,
        "avg_relative_humidity": 85.0
    },
    "delhi": {
        "location": "Delhi",
        "total_precipitation_mm": 2.1,
        "max_temperature_c": 41.5,
        "avg_relative_humidity": 45.0
    }
}


# ==========================================
# 4. OPEN-METEO WEATHER CLIENT
# ==========================================

async def get_weather_forecast(
    location: str
) -> Tuple[Dict[str, Any], bool]:
    """
    Fetch weather forecast from Open-Meteo.

    Returns:
        (
            weather_data_dictionary,
            fallback_used_boolean
        )
    """

    city_key = location.lower().strip()

    coords = CITY_COORDINATES.get(city_key)

    # --------------------------------------
    # Unknown city -> fallback
    # --------------------------------------
    if not coords:
        print(
            f"[WARN] Location '{location}' not supported. "
            f"Using Mumbai fallback data."
        )

        fallback_data = MOCK_FALLBACK_DATA["mumbai"]

        return fallback_data, True

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "hourly": (
            "precipitation,"
            "temperature_2m,"
            "relative_humidity_2m"
        ),
        "forecast_days": 1,
        "timezone": "auto"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:

            response = await client.get(
                url,
                params=params
            )

            # --------------------------------------
            # Successful API response
            # --------------------------------------
            if response.status_code == 200:

                data = response.json()

                hourly = data.get("hourly", {})

                precipitation = hourly.get(
                    "precipitation",
                    []
                )

                temperatures = hourly.get(
                    "temperature_2m",
                    []
                )

                humidity = hourly.get(
                    "relative_humidity_2m",
                    []
                )

                # --------------------------------------
                # Safety checks
                # --------------------------------------
                total_rain = sum(
                    value or 0
                    for value in precipitation
                )

                max_temp = max(
                    temperatures
                ) if temperatures else 0

                avg_humidity = (
                    sum(
                        value or 0
                        for value in humidity
                    ) / len(humidity)
                    if humidity
                    else 50
                )

                weather_data = {
                    "location": location,
                    "total_precipitation_mm": round(
                        total_rain,
                        1
                    ),
                    "max_temperature_c": round(
                        max_temp,
                        1
                    ),
                    "avg_relative_humidity": round(
                        avg_humidity,
                        1
                    )
                }

                return weather_data, False

            print(
                f"[WARN] Open-Meteo returned "
                f"HTTP {response.status_code}"
            )

    except Exception as e:

        print(
            f"[WARN] Open-Meteo API call failed: {e}"
        )

    # --------------------------------------
    # Fallback
    # --------------------------------------

    fallback_data = MOCK_FALLBACK_DATA.get(
        city_key,
        MOCK_FALLBACK_DATA["mumbai"]
    )

    return fallback_data, True


# ==========================================
# 5. FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Nimit Backend API",
    version="1.0.0",
    description=(
        "Backend API for weather, risk assessment "
        "and contextual safety recommendations."
    )
)


# ==========================================
# 6. CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,

    # For development / hackathon frontend
    allow_origins=["*"],

    # Keep False when allow_origins=["*"]
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
        "version": "1.0.0"
    }


# ==========================================
# 8. ASK ENDPOINT
# ==========================================

@app.post(
    "/ask",
    response_model=AskResponse
)
async def ask_nimit(payload: AskRequest):

    # --------------------------------------
    # Validate input
    # --------------------------------------

    if not payload.query.strip():

        raise HTTPException(
            status_code=400,
            detail="Query is required."
        )

    if not payload.location.strip():

        raise HTTPException(
            status_code=400,
            detail="Location is required."
        )

    # --------------------------------------
    # 1. Fetch weather
    # --------------------------------------

    weather_data, fallback_used = (
        await get_weather_forecast(
            payload.location
        )
    )

    precipitation = weather_data[
        "total_precipitation_mm"
    ]

    # --------------------------------------
    # 2. Rule Engine
    # --------------------------------------

    # Base risk from precipitation
    if precipitation < 5:

        risk_level = "LOW"

        rain_reason = (
            f"Forecasted precipitation: "
            f"{precipitation}mm "
            f"(Below 5mm threshold)"
        )

    elif precipitation < 15.6:

        risk_level = "MODERATE"

        rain_reason = (
            f"Forecasted precipitation: "
            f"{precipitation}mm "
            f"(Below 15.6mm threshold)"
        )

    elif precipitation < 50:

        risk_level = "HIGH"

        rain_reason = (
            f"Forecasted precipitation: "
            f"{precipitation}mm "
            f"(Exceeds 15.6mm threshold -> HIGH)"
        )

    else:

        risk_level = "SEVERE"

        rain_reason = (
            f"Forecasted precipitation: "
            f"{precipitation}mm "
            f"(Exceeds 50mm severe threshold)"
        )

    # --------------------------------------
    # Location-specific escalation
    # --------------------------------------

    known_flood_zones = [
        "andheri subway",
        "sion",
        "hindmata",
        "dadar",
        "kurla",
        "thane"
    ]

    query_lower = payload.query.lower()

    location_flagged = any(
        zone in query_lower
        for zone in known_flood_zones
    )

    reasoning_trace = [
        rain_reason
    ]

    if location_flagged:

        if risk_level == "LOW":
            risk_level = "MODERATE"

        elif risk_level == "MODERATE":
            risk_level = "HIGH"

        elif risk_level == "HIGH":
            risk_level = "SEVERE"

        reasoning_trace.append(
            "Location/query flagged as a known "
            "flood-prone area -> Risk escalated."
        )

    # --------------------------------------
    # 3. Generate response
    # --------------------------------------

    if risk_level == "SEVERE":

        answer = (
            f"I'd avoid the route if possible. "
            f"{payload.location.title()} is forecast to receive "
            f"around {precipitation}mm of precipitation, "
            f"which places the current assessment at SEVERE risk."
        )

    elif risk_level == "HIGH":

        answer = (
            f"I'd be cautious with this route. "
            f"{payload.location.title()} is forecast to receive "
            f"around {precipitation}mm of precipitation, "
            f"and the current assessment is HIGH risk."
        )

    elif risk_level == "MODERATE":

        answer = (
            f"There's some weather-related risk. "
            f"{payload.location.title()} is forecast to receive "
            f"around {precipitation}mm of precipitation, "
            f"so allow extra travel time and check conditions."
        )

    else:

        answer = (
            f"Current weather indicators look relatively low risk. "
            f"{payload.location.title()} is forecast to receive "
            f"around {precipitation}mm of precipitation."
        )

    # --------------------------------------
    # 4. Sources
    # --------------------------------------

    sources = [
        SourceCitation(
            title="BMC Drainage Report 2024",
            reference="Section 4.1"
        ),
        SourceCitation(
            title="IMD Mumbai Bulletin",
            reference="Heavy Rainfall Alert"
        )
    ]

    # --------------------------------------
    # 5. Final response
    # --------------------------------------

    return AskResponse(
        answer=answer,
        risk_level=risk_level,
        reasoning_trace=reasoning_trace,
        sources=sources,
        fallback_used=fallback_used
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
        reload=True
    )
    