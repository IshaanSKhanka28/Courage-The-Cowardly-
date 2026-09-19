"""Read-only verification of the retrieval layer."""

from retrieval.retrieve import retrieve_evidence


def show_results(label, results, expected_sector=None, expected_state=None):
    print(f"\n=== {label} ===")
    print(f"Results returned: {len(results)}")

    if not results:
        print("  (empty)")
        return

    flags = []
    for i, r in enumerate(results):
        snippet = (r.get("text") or "")[:120].replace("\n", " ")
        print(f"\n  --- Result #{i + 1} (distance={r.get('distance')}) ---")
        print(f"    source: {r.get('source')}")
        print(f"    type:   {r.get('type')}")
        print(f"    state:  {r.get('state')}")
        print(f"    city:   {r.get('city')}")
        print(f"    url:    {r.get('url_or_ref')}")
        print(f"    text:   \"{snippet}...\"")

        if expected_sector and r.get("sector") not in (expected_sector, None) and "sector" in r:
            flags.append(f"Result #{i+1} sector mismatch: expected {expected_sector}, got {r.get('sector')}")
        if expected_state and r.get("state") != expected_state:
            flags.append(f"Result #{i+1} state mismatch: expected {expected_state}, got {r.get('state')}")

    if flags:
        print("\n  FLAGS:")
        for f in flags:
            print(f"    - {f}")
    else:
        print("\n  No mismatches — location scoping looks correct.")


def main():
    # Case 1: known-good combination — should return real, correctly-tagged results
    r1 = retrieve_evidence(
        "will it flood tomorrow morning",
        sector="traffic", state="Maharashtra", city="Mumbai"
    )
    show_results("Mumbai traffic query (expect non-empty, Maharashtra-tagged)", r1,
                 expected_sector="traffic", expected_state="Maharashtra")

    # Case 2: health/Delhi — second known-good combination
    r2 = retrieve_evidence(
        "is it safe to be outdoors during a heatwave",
        sector="health", state="Delhi", city="Delhi"
    )
    show_results("Delhi health query (expect non-empty, Delhi-tagged)", r2,
                 expected_sector="health", expected_state="Delhi")

    # Case 3: a combination you know has NO curated docs — should return [] cleanly
    # Swap in a real gap in your coverage, e.g. an uncurated state for a sector.
    r3 = retrieve_evidence(
        "will it flood tomorrow",
        sector="traffic", state="Karnataka", city="Mysuru"  # adjust to an actual gap
    )
    show_results("Uncurated combination (expect EMPTY list)", r3)

    if r3:
        print("\n  *** WARNING: expected empty result, but got results. "
              "Retrieval may be leaking across locations. ***")
    else:
        print("\n  Correctly returned empty — no fabricated fallback.")

    # Case 4: no city given, state-wide fallback behavior
    r4 = retrieve_evidence(
        "wheat crop rain risk",
        sector="agriculture", state="Punjab", city=None
    )
    show_results("Punjab agriculture, no city specified (expect non-empty)", r4,
                  expected_sector="agriculture", expected_state="Punjab")


if __name__ == "__main__":
    main()