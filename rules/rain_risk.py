"""Waterlogging risk rules, derived from IMD rainfall categories."""

from dataclasses import dataclass, field

from rules.thresholds import RiskLevel, SourceType, classify_rainfall

_BASE_RISK_BY_CATEGORY = {
    "no_rain": RiskLevel.LOW,
    "light": RiskLevel.LOW,
    "moderate": RiskLevel.MODERATE,
    "heavy": RiskLevel.HIGH,
    "very_heavy": RiskLevel.HIGH,
    "extremely_heavy": RiskLevel.HIGH,
}

_ESCALATION = {
    RiskLevel.MODERATE: RiskLevel.HIGH,
    RiskLevel.HIGH: RiskLevel.SEVERE,
}


@dataclass
class RuleResult:
    risk_level: RiskLevel
    reasoning: list[str] = field(default_factory=list)
    source_tags: list[SourceType] = field(default_factory=list)
    raw_values: dict = field(default_factory=dict)


def evaluate_waterlogging_risk(rainfall_mm: float, is_known_flood_zone: bool) -> RuleResult:
    if rainfall_mm < 0:
        raise ValueError(f"rainfall_mm must be non-negative, got {rainfall_mm}")

    category = classify_rainfall(rainfall_mm)
    base_risk = _BASE_RISK_BY_CATEGORY[category]

    reasoning = [
        f"{rainfall_mm}mm of rainfall classifies as '{category}' per IMD 24hr rainfall bands",
        f"'{category}' maps to base risk {base_risk.value.upper()}",
    ]
    source_tags = [SourceType.OFFICIAL]

    risk_level = base_risk
    if is_known_flood_zone and base_risk in _ESCALATION:
        risk_level = _ESCALATION[base_risk]
        reasoning.append(
            f"Location is a known flood zone: escalating {base_risk.value.upper()} -> "
            f"{risk_level.value.upper()}"
        )
        source_tags.append(SourceType.DERIVED)

    return RuleResult(
        risk_level=risk_level,
        reasoning=reasoning,
        source_tags=source_tags,
        raw_values={
            "rainfall_mm": rainfall_mm,
            "rain_category": category,
            "is_known_flood_zone": is_known_flood_zone,
        },
    )
