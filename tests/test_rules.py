import pytest

from rules.thresholds import RiskLevel, SourceType, classify_rainfall
from rules.rain_risk import evaluate_waterlogging_risk
from rules.heat_risk import (
    heat_index_celsius,
    classify_heat_index,
    evaluate_outdoor_activity_risk,
)


class TestClassifyRainfall:
    def test_no_rain(self):
        assert classify_rainfall(0) == "no_rain"
        assert classify_rainfall(2.4) == "no_rain"

    def test_light(self):
        assert classify_rainfall(2.5) == "light"
        assert classify_rainfall(15.5) == "light"

    def test_extremely_heavy_open_ended(self):
        assert classify_rainfall(204.5) == "extremely_heavy"
        assert classify_rainfall(500) == "extremely_heavy"

    def test_negative_rainfall_rejected(self):
        with pytest.raises(ValueError):
            classify_rainfall(-1)


class TestWaterloggingRisk:
    def test_light_rain_no_flood_zone_is_low_risk(self):
        result = evaluate_waterlogging_risk(10.0, is_known_flood_zone=False)
        assert result.risk_level == RiskLevel.LOW
        assert SourceType.OFFICIAL in result.source_tags
        assert SourceType.DERIVED not in result.source_tags

    def test_heavy_rain_in_flood_zone_is_severe(self):
        result = evaluate_waterlogging_risk(80.0, is_known_flood_zone=True)
        assert result.risk_level == RiskLevel.SEVERE
        assert SourceType.DERIVED in result.source_tags
        assert any("escalat" in r.lower() for r in result.reasoning)

    def test_moderate_rain_in_flood_zone_escalates_to_high(self):
        result = evaluate_waterlogging_risk(30.0, is_known_flood_zone=True)
        assert result.risk_level == RiskLevel.HIGH
        assert SourceType.DERIVED in result.source_tags

    def test_negative_rainfall_rejected(self):
        with pytest.raises(ValueError):
            evaluate_waterlogging_risk(-5.0, is_known_flood_zone=False)


class TestHeatIndex:
    def test_classify_heat_index_bands(self):
        assert classify_heat_index(20) == "safe"
        assert classify_heat_index(30) == "caution"
        assert classify_heat_index(35) == "extreme_caution"
        assert classify_heat_index(45) == "danger"
        assert classify_heat_index(55) == "extreme_danger"

    def test_humidity_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            heat_index_celsius(30, -1)
        with pytest.raises(ValueError):
            heat_index_celsius(30, 101)


class TestOutdoorActivityRisk:
    def test_extreme_heat_is_severe(self):
        result = evaluate_outdoor_activity_risk(44.0, 60.0, involves_children=False)
        assert result.risk_level == RiskLevel.SEVERE

    def test_moderate_heat_with_children_escalates(self):
        result = evaluate_outdoor_activity_risk(33.0, 50.0, involves_children=True)
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.SEVERE)
        assert SourceType.DERIVED in result.source_tags

    def test_humidity_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            evaluate_outdoor_activity_risk(30.0, 150.0, involves_children=False)
