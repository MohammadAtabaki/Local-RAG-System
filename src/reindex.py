import os
import json
import hashlib
from chromadb_store import ChromaStore
from config import DATA_DIR

CACHE_PATH = os.path.join(DATA_DIR, ".index_cache.json")

def load_json_files(folder):
    files = []
    for fname in os.listdir(folder):
        if fname.endswith(".json") and not fname.startswith("."):
            full_path = os.path.join(folder, fname)
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                files.append((fname, content))
    return files

def flatten_pages(doc):
    results = []
    doc_context = doc.get("document_context", "")
    for page in doc.get("pages", []):
        for content in page.get("content", []):
            item = {
                "document_context": doc_context,
                "chapter_context": page.get("chapter_context", ""),
                "page_context": page.get("page_context", ""),
                "page_number": page.get("page_number", ""),
                **content
            }
            results.append(item)
    return results

def compute_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_cache():
    print("🔍 Loading cache...")
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("📦 Cached files:")
        for k, v in data.items():
            print(f"   - {k}: {v[:8]}...")
        return data
    return {}

def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def run_reindex():
    store = ChromaStore("./chroma_db")
    cache = load_cache()
    updated_cache = {}
    all_content = []

    for fname, content in load_json_files(DATA_DIR):
        doc_hash = compute_hash(content)
        updated_cache[fname] = doc_hash

        if cache.get(fname) == doc_hash:
            print(f"🟡 Skipping {fname} (unchanged)")
            continue

        print(f"✅ Reindexing {fname}...")
        try:
            parsed = json.loads(content)
            all_content.extend(flatten_pages(parsed))
        except Exception as e:
            print(f"❌ Error parsing {fname}: {e}")

    if all_content:
        store.add_documents(all_content)
        print(f"✅ Added {len(all_content)} content blocks to ChromaDB.")
    else:
        print("⚠️  No new documents were added.")

    save_cache(updated_cache)

if __name__ == "__main__":
    run_reindex()
