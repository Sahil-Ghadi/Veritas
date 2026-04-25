from sentence_transformers import SentenceTransformer, util

_model = None  # lazy load


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def check_essence_drift(essence: str, claims: list[dict]) -> dict:
    """
    Compare the article's core essence against the recomposed claims.
    If the claims lost the meaning (drift > 0.2), flag for re-split.

    Returns:
        {
          "passed": bool,
          "drift_score": float,   # 0 = perfect, 1 = completely different
        }
    """
    recomposed = " ".join(c["text"] for c in claims)

    model = _get_model()
    emb_essence = model.encode(essence, convert_to_tensor=True)
    emb_recomposed = model.encode(recomposed, convert_to_tensor=True)
    similarity = float(util.cos_sim(emb_essence, emb_recomposed).item())
    drift = round(1.0 - similarity, 4)

    return {
        "passed": drift <= 0.25,
        "drift_score": drift,
    }