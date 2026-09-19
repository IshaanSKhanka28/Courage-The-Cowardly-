"""Outdoor-activity heat risk rules, based on the NWS Rothfusz heat index
regression (https://www.weather.gov/ama/heatindex)."""

import math

from rules.rain_risk import RuleResult
from rules.thresholds import RiskLevel, SourceType

_CLASSIFICATION_THRESHOLDS_C = [
    (27.0, "safe"),
    (32.0, "caution"),
    (39.0, "extreme_caution"),
    (51.0, "danger"),
]

_BASE_RISK_BY_CLASS = {
    "safe": RiskLevel.LOW,
    "caution": RiskLevel.LOW,
    "extreme_caution": RiskLevel.MODERATE,
    "danger": RiskLevel.HIGH,
    "extreme_danger": RiskLevel.SEVERE,
}


def _validate_inputs(temp_c: float, humidity_pct: float) -> None:
    if not 0 <= humidity_pct <= 100:
        raise ValueError(f"humidity_pct must be between 0 and 100, got {humidity_pct}")


def heat_index_celsius(temp_c: float, humidity_pct: float) -> float:
    _validate_inputs(temp_c, humidity_pct)

    t_f = temp_c * 9.0 / 5.0 + 32.0
    rh = humidity_pct

    simple_hi_f = 0.5 * (t_f + 61.0 + (t_f - 68.0) * 1.2 + rh * 0.094)

    if (simple_hi_f + t_f) / 2.0 < 80.0:
        hi_f = simple_hi_f
    else:
        hi_f = (
            -42.379
            + 2.04901523 * t_f
            + 10.14333127 * rh
            - 0.22475541 * t_f * rh
            - 0.00683783 * t_f * t_f
            - 0.05481717 * rh * rh
            + 0.00122874 * t_f * t_f * rh
            + 0.00085282 * t_f * rh * rh
            - 0.00000199 * t_f * t_f * rh * rh
        )

        if rh < 13 and 80 <= t_f <= 112:
            adjustment = ((13 - rh) / 4.0) * math.sqrt((17 - abs(t_f - 95.0)) / 17.0)
            hi_f -= adjustment
        elif rh > 85 and 80 <= t_f <= 87:
            adjustment = ((rh - 85) / 10.0) * ((87 - t_f) / 5.0)
            hi_f += adjustment

    return (hi_f - 32.0) * 5.0 / 9.0


def classify_heat_index(hi_c: float) -> str:
    for threshold, label in _CLASSIFICATION_THRESHOLDS_C:
        if hi_c < threshold:
            return label
    return "extreme_danger"


def evaluate_outdoor_activity_risk(
    temp_c: float, humidity_pct: float, involves_children: bool
) -> RuleResult:
    _validate_inputs(temp_c, humidity_pct)

    hi_c = heat_index_celsius(temp_c, humidity_pct)
    classification = classify_heat_index(hi_c)
    base_risk = _BASE_RISK_BY_CLASS[classification]

    reasoning = [
        f"Heat index computed as {hi_c:.1f}C from temp={temp_c}C, humidity={humidity_pct}% "
        "via NWS Rothfusz regression",
        f"Heat index {hi_c:.1f}C classifies as '{classification}'",
        f"'{classification}' maps to base risk {base_risk.value.upper()}",
    ]
    source_tags = [SourceType.OFFICIAL]

    risk_level = base_risk
    if involves_children and base_risk == RiskLevel.MODERATE:
        risk_level = RiskLevel.HIGH
        reasoning.append(
            f"Activity involves children: escalating {base_risk.value.upper()} -> "
            f"{risk_level.value.upper()}"
        )
        source_tags.append(SourceType.DERIVED)

    return RuleResult(
        risk_level=risk_level,
        reasoning=reasoning,
        source_tags=source_tags,
        raw_values={
            "temp_c": temp_c,
            "humidity_pct": humidity_pct,
            "heat_index_c": hi_c,
            "heat_classification": classification,
            "involves_children": involves_children,
        },
    )
