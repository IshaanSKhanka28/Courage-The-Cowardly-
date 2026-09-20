import pytest

from rules.crop_risk import evaluate_crop_risk, CropRiskResult
from rules.rain_risk import RiskLevel, SourceType


class TestEvaluateCropRisk:
    def test_light_rain_low_risk(self):
        result = evaluate_crop_risk(rainfall_mm=5.0, crop_stage="grain_filling", is_unseasonal=False)
        assert result.risk_level == RiskLevel.LOW
        assert SourceType.DERIVED in result.source_tags

    def test_moderate_rain_modereate_risk_not_unseasonal(self):
        result = evaluate_crop_risk(rainfall_mm=30.0, crop_stage="grain_filling", is_unseasonal=False)
        assert result.risk_level == RiskLevel.MODERATE
        assert SourceType.DERIVED in result.source_tags

    def test_heavy_rain_high_risk_not_unseasonal(self):
        result = evaluate_crop_risk(rainfall_mm=80.0, crop_stage="grain_filling", is_unseasonal=False)
        assert result.risk_level == RiskLevel.HIGH
        assert SourceType.DERIVED in result.source_tags

    def test_heavy_unseasonal_rain_escalates_to_severe(self):
        """Heavy rain that is unseasonal during grain-filling should escalate to SEVERE."""
        result = evaluate_crop_risk(rainfall_mm=80.0, crop_stage="grain_filling", is_unseasonal=True)
        assert result.risk_level == RiskLevel.SEVERE
        assert SourceType.DERIVED in result.source_tags
        assert any("escalat" in r.lower() for r in result.reasoning)

    def test_moderate_unseasonal_rain_escalates_to_high(self):
        """Moderate rain that is unseasonal should escalate to HIGH."""
        result = evaluate_crop_risk(rainfall_mm=30.0, crop_stage="grain_filling", is_unseasonal=True)
        assert result.risk_level == RiskLevel.HIGH
        assert SourceType.DERIVED in result.source_tags
        assert any("escalat" in r.lower() for r in result.reasoning)

    def test_negative_rainfall_rejected(self):
        with pytest.raises(ValueError):
            evaluate_crop_risk(rainfall_mm=-5.0, crop_stage="grain_filling", is_unseasonal=False)

    def test_dry_no_risk(self):
        result = evaluate_crop_risk(rainfall_mm=0.0, crop_stage="grain_filling", is_unseasonal=True)
        assert result.risk_level == RiskLevel.LOW

    def test_very_heavy_unseasonal_severe(self):
        result = evaluate_crop_risk(rainfall_mm=200.0, crop_stage="grain_filling", is_unseasonal=True)
        assert result.risk_level == RiskLevel.SEVERE
        assert SourceType.DERIVED in result.source_tags

    def test_custom_crop_stage(self):
        result = evaluate_crop_risk(rainfall_mm=40.0, crop_stage="maturity", is_unseasonal=True)
        # 40mm is "moderate" -> unseasonal escalates MODERATE -> HIGH
        assert result.risk_level == RiskLevel.HIGH
        # Should mention the custom stage in reasoning
        assert "maturity" in " ".join(result.reasoning).lower()

    def test_unknown_crop_stage_defaults_grain_filling(self):
        result = evaluate_crop_risk(rainfall_mm=50.0, crop_stage="unknown_stage", is_unseasonal=True)
        # Unknown stage defaults to grain_filling assessment with a note
        assert any("unknown" in r.lower() or "grain_filling" in r.lower() for r in result.reasoning)
        assert result.risk_level == RiskLevel.HIGH  # 50mm moderate + unseasonal escalation