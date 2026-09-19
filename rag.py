"""
Tiny RAG pipeline:
1. Load each policy .md file
2. Split into chunks (one chunk per numbered rule - policies are already short lists)
3. Embed each chunk with Gemini's embedding model
4. Cache embeddings to disk so we don't re-call the API every run
5. At query time: embed the ticket text, compare via cosine similarity, return top-k chunks
"""
import re
import numpy as np
from google import genai

from .config import KB_DIR, EMBEDDINGS_PATH, GEMINI_API_KEY

_client = genai.Client(api_key=GEMINI_API_KEY)
EMBED_MODEL = "gemini-embedding-001"

_chunks: list[dict] = []      
_vectors: np.ndarray | None = None


def _load_and_chunk() -> list[dict]:
    """Split each policy file into one chunk per numbered rule (Ex. '1.', '2.', etc)."""
    chunks = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        rules = re.findall(r"^\d+\..*(?:\n(?!\d+\.).*)*", text, flags=re.MULTILINE)
        for rule in rules:
            rule = rule.strip()
            if rule:
                chunks.append({"text": rule, "source": path.name})
    return chunks


def _embed_texts(texts: list[str]) -> np.ndarray:
    result = _client.models.embed_content(model=EMBED_MODEL, contents=texts)
    return np.array([e.values for e in result.embeddings], dtype=np.float32)


def build_index(force: bool = False) -> None:
    """Build chunk embeddings. And, Call once at startup."""
    global _chunks, _vectors

    if EMBEDDINGS_PATH.exists() and not force:
        data = np.load(EMBEDDINGS_PATH, allow_pickle=True)
        _chunks = list(data["chunks"])
        _vectors = data["vectors"]
        return

    _chunks = _load_and_chunk()
    _vectors = _embed_texts([c["text"] for c in _chunks])
    np.savez(EMBEDDINGS_PATH, chunks=np.array(_chunks, dtype=object), vectors=_vectors)


def _cosine_sim(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
    return matrix_norm @ query_norm


def retrieve(ticket_text: str, top_k: int = 4) -> list[dict]:
    """Return the top_k most relevant policy chunks for this ticket."""
    if _vectors is None:
        build_index()

    query_vec = _embed_texts([ticket_text])[0]
    scores = _cosine_sim(query_vec, _vectors)
    top_idx = np.argsort(scores)[::-1][:top_k]

    return [
        {**_chunks[i], "score": float(scores[i])}
        for i in top_idx
    ]


if __name__ == "__main__":
    build_index(force=True)
    print(f"Indexed {len(_chunks)} policy chunks from {KB_DIR}")
    results = retrieve("My order arrived damaged and it's worth ₹5000")
    for r in results:
        print(f"[{r['score']:.3f}] ({r['source']}) {r['text'][:70]}...")

