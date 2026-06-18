from app.utils.constants import CHROMA_DIR

_collection = None
_fallback_store: list[dict] = []


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection("patient_memory")
        return _collection
    except Exception:
        return None


def add_memory(patient_id: int, text: str, metadata: dict | None = None) -> None:
    meta = metadata or {}
    meta["patient_id"] = patient_id
    collection = _get_collection()
    if collection is None:
        _fallback_store.append({"patient_id": patient_id, "text": text, "metadata": meta})
        return
    doc_id = f"{patient_id}_{len(_fallback_store)}"
    collection.add(documents=[text], metadatas=[meta], ids=[doc_id])


def query_memory(patient_id: int, query: str, n_results: int = 3) -> list[str]:
    collection = _get_collection()
    if collection is None:
        return [
            item["text"]
            for item in _fallback_store
            if item["patient_id"] == patient_id and query.lower() in item["text"].lower()
        ][:n_results]

    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"patient_id": patient_id},
        )
        return results.get("documents", [[]])[0]
    except Exception:
        return []
