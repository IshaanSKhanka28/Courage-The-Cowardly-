import os
import chromadb
from dotenv import load_dotenv

from rules.rain_risk import evaluate_waterlogging_risk
from rag.orchestrator import answer_query
from synthesis.synthesize import synthesize_answer

load_dotenv()

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("nimit_docs")

risk = evaluate_waterlogging_risk(rainfall_mm=42.0, is_known_flood_zone=True)

# If no Anthropic API key is in .env, use a mock client for demonstration
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("[NOTE] ANTHROPIC_API_KEY is not set in .env. Using mock Claude client for demonstration.\n")
    from tests.test_synthesize import FakeAnthropicClient

    fake_response = (
        "Given the high waterlogging risk in Mumbai, commuters should avoid low-lying underpasses. "
        "As reported by The Week and India TV News, Andheri Subway has experienced recurring closures "
        "and severe water accumulation during heavy rainfall.\n\n"
        "```json\n"
        '{"sources_cited": ["The Week", "India TV News"]}\n'
        "```"
    )
    fake_client = FakeAnthropicClient(response_text=fake_response)

    def custom_synthesizer(rule_res, evidence, query_text):
        return synthesize_answer(rule_res, evidence, query_text, client=fake_client)

    llm_fn = custom_synthesizer
else:
    llm_fn = synthesize_answer

result = answer_query(
    collection,
    sector="traffic",
    state="Maharashtra",
    city="Mumbai",
    risk_result=risk,
    query_text="will Andheri subway flood tomorrow",
    llm_fn=llm_fn,
)

print("--- Answer ---")
print(result["answer"])
print("\n--- Verified Sources ---")
print(result["sources"])
print(f"\n--- Total Evidence Chunks Retrieved: {len(result['evidence'])} ---")