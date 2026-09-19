"""Published thresholds used by the rule engine.

Rainfall bands: IMD (India Meteorological Department) 24-hour rainfall
classification, in millimetres.
"""

from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class SourceType(Enum):
    OFFICIAL = "official_threshold"
    DERIVED = "derived_composite"


# (min_mm, max_mm, label) — IMD 24hr rainfall bands. max_mm is None for the
# open-ended top band.
RAIN_CATEGORIES = [
    (0.0, 2.4, "no_rain"),
    (2.5, 15.5, "light"),
    (15.6, 64.4, "moderate"),
    (64.5, 115.5, "heavy"),
    (115.6, 204.4, "very_heavy"),
    (204.5, None, "extremely_heavy"),
]


def classify_rainfall(mm: float) -> str:
    if mm < 0:
        raise ValueError(f"rainfall_mm must be non-negative, got {mm}")

    for min_mm, max_mm, label in RAIN_CATEGORIES:
        if max_mm is None:
            if mm >= min_mm:
                return label
        elif min_mm <= mm <= max_mm:
            return label

    raise ValueError(f"rainfall_mm {mm} did not match any IMD category")
