"""Verification script for ChromaDB ingestion.

Performs read-only checks on the Chroma collection at ./chroma_db:
1. Connects to the existing collection ('nimit_docs').
2. Pulls 5 sample chunks via collection.get(limit=5) and prints each chunk's
   full metadata (SOURCE, TYPE, SECTOR, STATE, CITY, URL_OR_REF) plus the first
   150 chars of its text.
3. Runs a test query: collection.query(query_texts=["will it flood in Andheri tomorrow"], n_results=3)
   and prints each result's SOURCE, CITY, and first 150 chars.
4. Flags explicitly if any metadata field is None or missing on any sample.
"""

import sys
import chromadb

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "nimit_docs"
REQUIRED_FIELDS = ["SOURCE", "TYPE", "SECTOR", "STATE", "CITY", "URL_OR_REF"]


def get_field_val(metadata: dict, field_name: str):
    """Retrieves field value checking uppercase or lowercase keys."""
    if field_name in metadata:
        return metadata[field_name]
    if field_name.lower() in metadata:
        return metadata[field_name.lower()]
    return None


def check_metadata_flags(metadata: dict | None, chunk_id: str) -> list[str]:
    """Flags if any required metadata field is None or missing."""
    flags = []
    if metadata is None:
        flags.append(f"FLAG: metadata dictionary is None for ID '{chunk_id}'")
        return flags

    for field in REQUIRED_FIELDS:
        if field not in metadata and field.lower() not in metadata:
            flags.append(f"FLAG: field '{field}' is MISSING in metadata for ID '{chunk_id}'")
        else:
            val = get_field_val(metadata, field)
            if val is None:
                flags.append(f"FLAG: field '{field}' is None in metadata for ID '{chunk_id}'")
    return flags


def main():
    print("=" * 80)
    print("CHROMA INGESTION VERIFICATION")
    print("=" * 80)

    # 1. Connect to ChromaDB
    print(f"\n[1] Connecting to Chroma collection at: {CHROMA_PATH} ...")
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        print(f"    Available collections: {collection_names}")

        if COLLECTION_NAME in collection_names:
            collection = client.get_collection(name=COLLECTION_NAME)
        elif len(collections) > 0:
            collection = collections[0]
            print(f"    Target '{COLLECTION_NAME}' not found, using collection: '{collection.name}'")
        else:
            print("    ERROR: No collections found in ./chroma_db.")
            sys.exit(1)

        total_count = collection.count()
        print(f"    Connected to collection '{collection.name}' (Total chunks: {total_count})")
    except Exception as e:
        print(f"    ERROR connecting to Chroma collection: {e}")
        sys.exit(1)

    # 2. Pull 5 sample chunks
    print("\n" + "=" * 80)
    print("[2] Pulling 5 sample chunks via collection.get(limit=5)...")
    print("=" * 80)

    samples = collection.get(limit=5, include=["metadatas", "documents"])
    ids = samples.get("ids", [])
    metadatas = samples.get("metadatas", [])
    documents = samples.get("documents", [])

    all_flags = []

    for i in range(len(ids)):
        chunk_id = ids[i]
        meta = metadatas[i] if i < len(metadatas) else None
        doc = documents[i] if i < len(documents) else ""
        first_150 = doc[:150].replace("\n", " ") if doc else ""

        print(f"\n--- Sample Chunk #{i + 1} (ID: {chunk_id}) ---")
        if meta:
            print(f"  SOURCE     : {get_field_val(meta, 'SOURCE')}")
            print(f"  TYPE       : {get_field_val(meta, 'TYPE')}")
            print(f"  SECTOR     : {get_field_val(meta, 'SECTOR')}")
            print(f"  STATE      : {get_field_val(meta, 'STATE')}")
            print(f"  CITY       : {get_field_val(meta, 'CITY')}")
            print(f"  URL_OR_REF : {get_field_val(meta, 'URL_OR_REF')}")
            # print other extra keys if present
            extra_keys = [k for k in meta.keys() if k not in REQUIRED_FIELDS and k.upper() not in REQUIRED_FIELDS]
            if extra_keys:
                extras = {k: meta[k] for k in extra_keys}
                print(f"  EXTRA_META : {extras}")
        else:
            print("  METADATA   : <NONE>")

        flags = check_metadata_flags(meta, chunk_id)
        if flags:
            for flag in flags:
                print(f"  >> {flag}")
            all_flags.extend(flags)
        else:
            print("  >> METADATA STATUS : ALL REQUIRED FIELDS PRESENT & NON-NULL")

        print(f"  TEXT (first 150 chars):")
        print(f"  \"{first_150}...\"" if len(doc) > 150 else f"  \"{first_150}\"")

    # Summary of sample flags
    print("\n" + "-" * 80)
    if all_flags:
        print(f"WARNING: Found {len(all_flags)} metadata flag(s) across sample chunks:")
        for flag in all_flags:
            print(f"  - {flag}")
    else:
        print("SUMMARY: 0 metadata flags found across all 5 sample chunks.")

    # 3. Test Query
    test_query = "will it flood in Andheri tomorrow"
    n_results = 3
    print("\n" + "=" * 80)
    print(f"[3] Running test query: collection.query(query_texts=['{test_query}'], n_results={n_results})")
    print("=" * 80)

    try:
        query_res = collection.query(query_texts=[test_query], n_results=n_results)
        q_ids = query_res.get("ids", [[]])[0]
        q_metas = query_res.get("metadatas", [[]])[0]
        q_docs = query_res.get("documents", [[]])[0]
        q_dists = query_res.get("distances", [[]])[0] if "distances" in query_res and query_res["distances"] else []

        for j in range(len(q_ids)):
            res_id = q_ids[j]
            res_meta = q_metas[j] if j < len(q_metas) else {}
            res_doc = q_docs[j] if j < len(q_docs) else ""
            res_dist = q_dists[j] if j < len(q_dists) else "N/A"
            res_150 = res_doc[:150].replace("\n", " ") if res_doc else ""

            source = get_field_val(res_meta, "SOURCE") if res_meta else None
            city = get_field_val(res_meta, "CITY") if res_meta else None

            print(f"\n--- Query Result #{j + 1} (Distance: {res_dist}) ---")
            print(f"  SOURCE          : {source}")
            print(f"  CITY            : {city}")

            q_flags = check_metadata_flags(res_meta, res_id)
            if q_flags:
                for qf in q_flags:
                    print(f"  >> {qf}")
            else:
                print("  >> METADATA     : ALL REQUIRED FIELDS PRESENT & NON-NULL")

            print(f"  TEXT (first 150 chars):")
            print(f"  \"{res_150}...\"" if len(res_doc) > 150 else f"  \"{res_150}\"")

    except Exception as e:
        print(f"    ERROR executing test query: {e}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
