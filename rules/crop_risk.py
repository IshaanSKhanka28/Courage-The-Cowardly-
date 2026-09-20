"""Agricultural risk rules, based on curated advisory documents for wheat
cultivation in Punjab and IMD 24-hour rainfall classification.

Refs: ICAR-CRIDA district contingency plans, PAU Package of Practices, and
The Tribune news advisories on unseasonal rain & wind damage to wheat.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rules.rain_risk import RiskLevel, SourceType, classify_rainfall
from rules.thresholds import RiskLevel as GlobalRiskLevel

__all__ = ["evaluate_crop_risk", "CropRiskResult"]

#: Crop stages known to be vulnerable to rain/wind-induced lodging/disease,
#: per the curated advisory documents (ICAR-CRIDA contingency plans, PAU
#: Package of Practices, The Tribune reports).
_VULNERABLE_STAGES = frozenset({"grain_filling", "hard_dough", "maturity", "post-harvest"})


# ---------------------------------------------------------------------------
# Threshold mapping: we use the IMD 24-hour rainfall bands as the base
# categorisation, then apply crop-stage + unseasonal escalation.  The IMD
# bands are the de facto standard referenced in the curated docs (see
# docs/agriculture/… IMD SOP, bulletin metadata, etc.).
# ---------------------------------------------------------------------------

_BASE_RISK_BY_CATEGORY: dict[str, RiskLevel] = {
    "no_rain": RiskLevel.LOW,
    "light": RiskLevel.LOW,
    "moderate": RiskLevel.MODERATE,
    "heavy": RiskLevel.HIGH,
    "very_heavy": RiskLevel.HIGH,
    "extremely_heavy": RiskLevel.SEVERE,
}


# ---------------------------------------------------------------------------
# Escalation: if is_unseasonal is True and base risk is MODERATE or higher,
# escalate one level.  Mirrors the pattern in rules/rain_risk.py.
# ---------------------------------------------------------------------------

_ESCALATION: dict[RiskLevel, RiskLevel] = {
    RiskLevel.MODERATE: RiskLevel.HIGH,
    RiskLevel.HIGH: RiskLevel.SEVERE,
    RiskLevel.SEVERE: RiskLevel.SEVERE,
}


@dataclass
class CropRiskResult:
    risk_level: RiskLevel
    reasoning: list[str] = field(default_factory=list)
    source_tags: list[SourceType] = field(default_factory=list)
    raw_values: dict = field(default_factory=dict)


def evaluate_crop_risk(
    rainfall_mm: float,
    crop_stage: str = "grain_filling",
    is_unseasonal: bool = True,
) -> CropRiskResult:
    """Evaluate agricultural risk from rainfall for a given crop stage.

    Grounded in the curated advisory documents under docs/agriculture/:
    - ICAR-CRIDA & PAU district contingency plans warn of "continuous high
      rainfall in a short span" and "heavy rainfall with high speed winds"
      during wheat's grain-filling / hard dough / maturity stages, causing
      lodging and disease risk.
    - PAU Package of Practices cautions against irrigating on windy days to
      avoid lodging at grain-filling stage; ties yellow-rust disease severity
      to "frequent rains along with wind during February-March".
    - The Tribune reports consistently link unseasonal heavy rain + wind
      during wheat's mature stage with lodging and quality degradation.

    If a specific mm threshold is not stated in the official documents, the
    IMD 24-hour rainfall bands are used as the objective basis, and the
    source is tagged SourceType.DERIVED with an explicit reasoning note.

    Base risk from precipitation (IMD categories):
      - no_rain / light                 -> LOW
      - moderate                        -> MODERATE
      - heavy / very_heavy              -> HIGH
      - extremely_heavy                 -> SEVERE

    Elevation logic:
      - If *crop_stage* is a known vulnerable stage
        (grain_filling, hard_dough, maturity, post-harvest) and rain is
        at least moderate, base risk is kept as-is but escalation may apply.
      - If *is_unseasonal* is True and base_risk is MODERATE or higher,
        escalate one level (MODERATE->HIGH, HIGH->SEVERE, SEVERE->SEVERE),
        mirroring the escalation pattern in rules/rain_risk.py.
      - Unknown crop_stage defaults to "grain_filling" (the most common
        vulnerable stage per the docs) and is logged in reasoning.

    Args:
        rainfall_mm: precipitation in millimetres (must be >= 0).
        crop_stage: one of "grain_filling", "hard_dough", "maturity",
            "post-harvest", or any other string (defaults to "grain_filling").
        is_unseasonal: whether the rain event is unseasonal for the time of
            year.  When True and base risk is MODERATE+, escalates one level.

    Returns:
        A CropRiskResult dataclass with risk_level, reasoning, and source_tags.

    Raises:
        ValueError: if *rainfall_mm* is negative.
    """
    if rainfall_mm < 0:
        raise ValueError(f"rainfall_mm must be non-negative, got {rainfall_mm}")

    category = classify_rainfall(rainfall_mm)
    base_risk = _BASE_RISK_BY_CATEGORY[category]

    reasoning: list[str] = [
        f"{rainfall_mm}mm of rainfall classifies as '{category}' per IMD 24hr "
        "rainfall bands",
        f"'{category}' maps to base risk {base_risk.value.upper()}",
    ]

    # If the crop stage is one we know is vulnerable to rain/wind damage,
    # explicitly note it; otherwise default to grain_filling and flag it.
    if crop_stage in _VULNERABLE_STAGES:
        reasoning.append(
            f"Crop stage '{crop_stage}' is a known vulnerable stage for "
            "rain/wind-induced lodging/disease per curated advisory documents"
        )
    else:
        reasoning.append(
            f"Crop stage '{crop_stage}' not in known vulnerable stages; "
            "defaulting to grain_filling assessment"
        )
        crop_stage = "grain_filling"

    source_tags: list[SourceType] = [SourceType.DERIVED]

    risk_level = base_risk
    if is_unseasonal and base_risk in _ESCALATION:
        risk_level = _ESCALATION[base_risk]
        reasoning.append(
            f"Unseasonal rain: escalating {base_risk.value.upper()} -> "
            f"{risk_level.value.upper()}"
        )

    return CropRiskResult(
        risk_level=risk_level,
        reasoning=reasoning,
        source_tags=source_tags,
        raw_values={
            "rainfall_mm": rainfall_mm,
            "rain_category": category,
            "crop_stage": crop_stage,
            "is_unseasonal": is_unseasonal,
        },
    )