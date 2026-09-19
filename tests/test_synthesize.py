import anthropic
import pytest

from rules.rain_risk import RuleResult
from rules.thresholds import RiskLevel
from synthesis.synthesize import (
    NO_ADVISORY_FALLBACK_TEMPLATE,
    _parse_model_output,
    synthesize_answer,
    verify_citations,
)


class _FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text):
        self.content = [_FakeTextBlock(text)]


class _FakeMessages:
    def __init__(self, response_text=None, exception=None):
        self.response_text = response_text
        self.exception = exception
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exception is not None:
            raise self.exception
        return _FakeResponse(self.response_text)


class FakeAnthropicClient:
    def __init__(self, response_text=None, exception=None):
        self.messages = _FakeMessages(response_text=response_text, exception=exception)


SAMPLE_EVIDENCE = [
    {
        "text": "Andheri Subway has flooded repeatedly during heavy monsoon rain.",
        "source": "The Week",
        "type": "news_secondary",
        "state": "Maharashtra",
        "city": "Mumbai",
        "url_or_ref": "https://www.theweek.in/example",
        "distance": 0.42,
    },
    {
        "text": "BMC's stormwater drains were designed for 25mm/hour of rainfall.",
        "source": "Citizen Matters",
        "type": "news_secondary",
        "state": "Maharashtra",
        "city": "Mumbai",
        "url_or_ref": "https://citizenmatters.in/example",
        "distance": 0.51,
    },
]


def _make_rule_result(risk_level=RiskLevel.HIGH, reasoning=None):
    return RuleResult(
        risk_level=risk_level,
        reasoning=reasoning or ["42mm classifies as moderate rainfall.", "Escalated due to flood zone."],
    )


class TestEmptyEvidenceFallback:
    def test_empty_evidence_never_calls_llm(self):
        client = FakeAnthropicClient(response_text="THIS SHOULD NEVER BE USED")
        rule_result = _make_rule_result(risk_level=RiskLevel.HIGH)

        synthesize_answer(rule_result, [], "Is it safe to drive right now?", client=client)

        assert client.messages.calls == [], "LLM must not be called when evidence is empty"

    def test_empty_evidence_returns_exact_honest_fallback(self):
        client = FakeAnthropicClient(response_text="THIS SHOULD NEVER BE USED")
        rule_result = _make_rule_result(risk_level=RiskLevel.SEVERE)

        result = synthesize_answer(rule_result, [], "Any flooding advisories?", client=client)

        assert result == {
            "answer": NO_ADVISORY_FALLBACK_TEMPLATE.format(risk_level="severe"),
            "sources": [],
            "risk_level": "severe",
        }


class TestVerifyCitations:
    def test_drops_fabricated_source_not_in_evidence(self):
        result = verify_citations(["The Week", "A Source That Was Never Retrieved"], SAMPLE_EVIDENCE)

        names = {item["source"] for item in result}
        assert names == {"The Week"}

    def test_keeps_source_name_that_matches_evidence(self):
        result = verify_citations(["Citizen Matters"], SAMPLE_EVIDENCE)

        assert len(result) == 1
        assert result[0]["source"] == "Citizen Matters"
        assert result[0]["url_or_ref"] == "https://citizenmatters.in/example"

    def test_empty_claims_returns_empty_list(self):
        assert verify_citations([], SAMPLE_EVIDENCE) == []

    def test_duplicate_claims_are_deduplicated(self):
        result = verify_citations(["The Week", "The Week"], SAMPLE_EVIDENCE)
        assert len(result) == 1


class TestParseModelOutput:
    def test_extracts_answer_and_sources_from_fenced_json_block(self):
        raw = (
            "Given the heavy rain, I'd be cautious near Andheri.\n\n"
            '```json\n{"sources_cited": ["The Week", "Citizen Matters"]}\n```'
        )
        answer, sources = _parse_model_output(raw)

        assert answer == "Given the heavy rain, I'd be cautious near Andheri."
        assert sources == ["The Week", "Citizen Matters"]

    def test_missing_json_block_returns_full_text_and_no_sources(self):
        raw = "Just a plain conversational answer with no trailing JSON."
        answer, sources = _parse_model_output(raw)

        assert answer == raw
        assert sources == []

    def test_malformed_json_block_falls_back_to_no_sources_not_a_crash(self):
        raw = 'Some answer text.\n\n```json\n{"sources_cited": [BROKEN\n```'
        answer, sources = _parse_model_output(raw)

        assert "Some answer text." in answer
        assert sources == []


class TestSynthesizeAnswerHappyPath:
    def test_calls_llm_and_returns_verified_sources(self):
        raw_response = (
            "Given the moderate rainfall and the flood zone escalation, I'd avoid Andheri "
            "Subway for now - The Week reported it floods repeatedly in heavy monsoon rain.\n\n"
            '```json\n{"sources_cited": ["The Week"]}\n```'
        )
        client = FakeAnthropicClient(response_text=raw_response)
        rule_result = _make_rule_result(risk_level=RiskLevel.HIGH)

        result = synthesize_answer(
            rule_result, SAMPLE_EVIDENCE, "Is Andheri subway flooded right now?", client=client
        )

        assert "Forecast:" not in result["answer"]
        assert "Risk:" not in result["answer"]
        assert "```json" not in result["answer"]
        assert result["risk_level"] == "high"
        assert [s["source"] for s in result["sources"]] == ["The Week"]
        assert len(client.messages.calls) == 1

    def test_fabricated_source_claimed_by_llm_is_not_surfaced(self):
        raw_response = (
            "Here's the situation.\n\n"
            '```json\n{"sources_cited": ["A Source That Was Never Retrieved"]}\n```'
        )
        client = FakeAnthropicClient(response_text=raw_response)
        rule_result = _make_rule_result()

        result = synthesize_answer(rule_result, SAMPLE_EVIDENCE, "query", client=client)

        assert result["sources"] == []

    def test_passes_model_override_through_to_client(self):
        raw_response = 'Answer.\n\n```json\n{"sources_cited": []}\n```'
        client = FakeAnthropicClient(response_text=raw_response)
        rule_result = _make_rule_result()

        synthesize_answer(rule_result, SAMPLE_EVIDENCE, "query", client=client, model="claude-haiku-4-5-20251001")

        assert client.messages.calls[0]["model"] == "claude-haiku-4-5-20251001"


class TestSynthesizeAnswerErrorHandling:
    def test_api_error_returns_error_state_not_a_crash(self):
        client = FakeAnthropicClient(
            exception=anthropic.APIConnectionError(request=None)
        )
        rule_result = _make_rule_result(risk_level=RiskLevel.MODERATE)

        result = synthesize_answer(rule_result, SAMPLE_EVIDENCE, "query", client=client)

        assert result["sources"] == []
        assert result["risk_level"] == "moderate"
        assert "raw_error" in result

    def test_raw_exception_text_is_not_leaked_into_user_facing_answer(self):
        secret_looking_error = anthropic.AuthenticationError(
            message="invalid x-api-key: sk-ant-super-secret-do-not-leak",
            response=_FakeAuthErrorResponse(),
            body=None,
        )
        client = FakeAnthropicClient(exception=secret_looking_error)
        rule_result = _make_rule_result()

        result = synthesize_answer(rule_result, SAMPLE_EVIDENCE, "query", client=client)

        assert "sk-ant-super-secret-do-not-leak" not in result["answer"]
        assert "sk-ant-super-secret-do-not-leak" in result["raw_error"]


class _FakeAuthErrorResponse:
    """Minimal stand-in for an httpx.Response, just enough for
    anthropic.APIStatusError's constructor to not blow up."""

    status_code = 401
    headers = {}
    request = None
