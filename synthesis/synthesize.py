"""Synthesis layer for Nimit: turns rule-engine output + retrieved evidence
into a short, conversational, citation-verified answer.

Consumes (but does not import or call) the output shapes of:
    - rules/*.py            RuleResult(risk_level, reasoning, source_tags, raw_values)
    - retrieval/retrieve.py retrieve_evidence(...) -> list[dict] with keys
                             text, source, type, state, city, url_or_ref, distance

Nothing here talks to Chroma or the rule engine directly - both are passed
in by the caller. This keeps the module testable without a live vector store
and keeps rules/ and retrieval/ untouched.

Two paths, and only two:
    1. evidence is empty -> a hardcoded, fully deterministic fallback.
       The LLM is never called on this path, full stop - there is nothing
       for it to be grounded in, so calling it would just invite it to
       improvise a "local advisory" that doesn't exist.
    2. evidence is non-empty -> Claude drafts a conversational answer citing
       only the given evidence, and verify_citations() strips any source
       name it claims that isn't actually backed by a retrieved chunk before
       that source is ever surfaced to the user.
"""

import json
import logging
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("NIMIT_SYNTHESIS_MODEL", "claude-sonnet-5")
MAX_TOKENS = 1024

NO_ADVISORY_FALLBACK_TEMPLATE = (
    "Based on the forecast, risk level is {risk_level}. I don't have a "
    "verified local advisory on file for this location yet."
)

LLM_ERROR_FALLBACK_TEMPLATE = (
    "I ran into a technical problem generating a grounded answer just now, "
    "so I don't want to guess. Here's what I can tell you from the forecast "
    "alone: the computed risk level is {risk_level}."
)

SYSTEM_PROMPT = """You are Nimit, a friendly local weather-risk assistant for India. \
You explain flood, heatwave, and crop risk the way a knowledgeable friend would: in \
short, natural, conversational sentences - never as a labeled report with fields like \
"Forecast:", "Risk:", or "Recommendation:". Weave the reasoning and any caveats \
naturally into your sentences instead of listing them out.

STYLE AND VARIETY: Do not reuse a stock opening such as "Based on the risk assessment" \
or "Please exercise caution." Start with the clearest human answer for this particular \
question: "I'd avoid it", "I'd hold off", "There is some risk here", or an equally \
natural alternative. Vary sentence openings and connective phrases across answers. Use \
the useful concrete values from the risk reasoning when available (rainfall, heat index, \
temperature, timing, or threshold), and explain why they matter in plain language. Give \
one or two practical next steps suited to the question. For high or severe risk, be \
decisive; for moderate risk, be measured; for low risk, say what is reasonably safe. \
Do not pad the answer with generic reminders or repeat the same conclusion in different \
words. Acknowledge an assumption when the evidence does not establish a detail such as \
the user's exact route, crop stage, or timing.

You are given three things:
1. A computed risk level and the deterministic reasoning behind it. Treat this as \
established fact - never contradict, soften, or second-guess it.
2. A numbered list of retrieved evidence snippets, each with a SOURCE name, its TYPE, \
and a URL. This is the ONLY material you may cite. Never mention, reference, or imply \
a source, quote, statistic, or URL that is not in this list. If none of the evidence \
is relevant to some part of the question, simply don't mention it rather than \
inventing something to fill the gap.
3. The user's question.

WRITE IN OWN WORDS - NEVER quote retrieved source text verbatim, even with quotation marks.
Instead of 'As noted by The Week: "..."', paraphrase into your own words, e.g.:
"Local reports from BMC confirm this area has flooded during similarly heavy rainfall before."
If you must name a source, attach it to your paraphrase (e.g. "as BMC's guidelines note...").

SPECIFICITY GAP - If the user's query names a specific route, street, neighborhood, or \
landmark that is MORE SPECIFIC than what the retrieved evidence actually covers (e.g. \
evidence is city-wide but the query asks about one locality), explicitly acknowledge \
that gap. Example: "I have Mumbai-wide monsoon risk data, but I cannot confirm the \
specific conditions on your exact route. For general guidance: allow extra travel time \
and check conditions." Never imply city-wide data confirms something about a specific place.

HISTORICAL PRECEDENT - When retrieved evidence references a dated past event (e.g. a \
specific flooding incident from a past date), never present it as if it directly \
confirms something will happen "tomorrow" or "today." Frame it explicitly as \
historical precedent: "this area has flooded in similar rainfall conditions before" - \
not as if the past event itself is the current forecast.

DIRECT ANSWER - The answer must directly address what was actually asked (e.g. "will I \
face traffic") rather than defaulting to generic boilerplate like "please exercise \
caution... stay tuned to local advisories" when that doesn't actually answer the \
specific question.

FEW-SHOT EXAMPLES (showing the correct paraphrased, honest-about-scope style vs the wrong quoted/vague style):

QUESTION: "will I face traffic in Mumbai during heavy rainfall"
RIGHT: "Local reports from BMC confirm Mumbai has a history of waterlogging during heavy rain, especially in low-lying underpasses like the Andheri Subway. I cannot confirm your exact route, but the general guidance is to allow extra travel time and check conditions before you set out."
WRONG: 'As noted by The Week: "Mumbai Rain Disruptions..."'

QUESTION: "is it safe for children to play outside in Delhi during a heatwave"
RIGHT: "Delhi's heat index is currently in the 'danger' range per IMD criteria, and standing heat particularly affects children. The advisory recommends staying indoors during peak afternoon hours and keeping hydrated."
WRONG: 'As noted by NDMA guidelines: "Heatwave conditions are dangerous."'

QUESTION: "will the flooding from yesterday's rain still be around today"
RIGHT: "This area has a history of waterlogging that persists after heavy rain, as BMC's guidelines note - drainage can take over 24 hours to fully clear. Allow extra time if you must travel."
WRONG: "The July 2024 flooding in Mumbai will happen again today."

After your conversational answer, on its own lines, append a JSON block in exactly \
this form, listing only the SOURCE names you actually cited (verbatim, exactly as \
given), or an empty array if you cited none:

```json
{"sources_cited": ["Exact Source Name One", "Exact Source Name Two"]}
```
"""

_JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
_TRAILING_BRACE_RE = re.compile(r"(\{[^{}]*\"sources_cited\"[^{}]*\})\s*$", re.DOTALL)


def _risk_level_value(rule_result) -> str:
    risk_level = rule_result.risk_level
    return getattr(risk_level, "value", risk_level)


def _format_evidence_block(evidence: list[dict]) -> str:
    entries = []
    for i, item in enumerate(evidence, start=1):
        entries.append(
            f"[{i}] SOURCE: {item.get('source')} | TYPE: {item.get('type')} | "
            f"URL: {item.get('url_or_ref')}\n{item.get('text', '').strip()}"
        )
    return "\n\n".join(entries)


def _build_user_message(rule_result, evidence: list[dict], user_query: str) -> str:
    reasoning_block = "\n".join(f"- {line}" for line in rule_result.reasoning)
    evidence_block = _format_evidence_block(evidence)

    return f"""RISK ASSESSMENT (established fact, do not contradict):
Risk level: {_risk_level_value(rule_result)}
Reasoning:
{reasoning_block}

RETRIEVED EVIDENCE (the only sources you may cite):
{evidence_block}

USER QUESTION:
{user_query}

Write a short, conversational answer (3-6 sentences) grounded only in the risk \
assessment and evidence above. It should read like a knowledgeable person answering \
this exact question, not like a report template. Then append the sources_cited JSON \
block exactly as instructed."""


def _call_claude(system_prompt: str, user_message: str, client, model: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


def _parse_model_output(raw_text: str) -> tuple[str, list[str]]:
    """Splits Claude's reply into (conversational answer, claimed source names).

    Tolerates a missing or malformed trailing JSON block: falls back to an
    empty claimed-sources list (never invents one) and still returns the
    conversational text with the block/fence stripped where it was found.
    """
    match = _JSON_FENCE_RE.search(raw_text)
    if match is None:
        match = _TRAILING_BRACE_RE.search(raw_text)

    if match is None:
        return raw_text.strip(), []

    json_str = match.group(1)
    answer = raw_text[: match.start()].rstrip()

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("Could not parse sources_cited JSON block from model output: %r", json_str)
        return answer, []

    claimed = parsed.get("sources_cited", [])
    if not isinstance(claimed, list):
        logger.warning("sources_cited was not a list: %r", claimed)
        return answer, []

    return answer, [s for s in claimed if isinstance(s, str)]


def verify_citations(claimed_sources: list[str], evidence: list[dict]) -> list[dict]:
    """Keeps only claimed source names that match a SOURCE field actually
    present in the retrieved evidence. Anything the model claims that isn't
    backed by a real retrieved chunk is dropped and logged - it should never
    happen given the prompt, but this is the layer that catches it if it does.
    """
    evidence_by_source: dict[str, dict] = {}
    for item in evidence:
        source_name = item.get("source")
        if source_name and source_name not in evidence_by_source:
            evidence_by_source[source_name] = item

    verified = []
    seen = set()
    for name in claimed_sources:
        if name in evidence_by_source:
            if name not in seen:
                verified.append(evidence_by_source[name])
                seen.add(name)
        else:
            logger.warning(
                "LLM claimed a source not present in retrieved evidence - dropping it: %r",
                name,
            )

    return verified


def synthesize_answer(
    rule_result,
    evidence: list[dict],
    user_query: str,
    client=None,
    model: str | None = None,
) -> dict:
    """Returns {answer: str, sources: list[dict], risk_level: str}.

    On an empty evidence list, this is fully deterministic - no LLM call is
    made. On a non-empty list, Claude drafts an answer and every source it
    claims to cite is checked against the real evidence before being
    returned; unverified claims are silently dropped (and logged).

    On an API failure (network, rate limit, bad key, etc.) this catches the
    error and returns an honest error-state response instead of raising -
    the raw exception text is included only in `raw_error`, never in the
    user-facing `answer`.
    """
    risk_level = _risk_level_value(rule_result)

    if not evidence:
        return {
            "answer": NO_ADVISORY_FALLBACK_TEMPLATE.format(risk_level=risk_level),
            "sources": [],
            "risk_level": risk_level,
        }

    model = model or DEFAULT_MODEL
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    user_message = _build_user_message(rule_result, evidence, user_query)

    try:
        raw_text = _call_claude(SYSTEM_PROMPT, user_message, client, model)
    except anthropic.AnthropicError as e:
        logger.error("Anthropic API call failed during synthesis: %s", e)
        return {
            "answer": LLM_ERROR_FALLBACK_TEMPLATE.format(risk_level=risk_level),
            "sources": [],
            "risk_level": risk_level,
            "raw_error": str(e),
        }

    answer_text, claimed_sources = _parse_model_output(raw_text)
    verified_sources = verify_citations(claimed_sources, evidence)

    if verified_sources:
        source_names = ", ".join(source["source"] for source in verified_sources)
        answer_text = f"{answer_text.rstrip()}\n\nSources: {source_names}"

    return {
        "answer": answer_text,
        "sources": verified_sources,
        "risk_level": risk_level,
    }
