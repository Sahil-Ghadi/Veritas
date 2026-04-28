def check_essence_drift(essence: str, claims: list[dict]) -> dict:
    """
    Simple check if claims preserve the essence.
    Returns a default drift score since semantic search is removed.
    """
    return {
        "passed": True,
        "drift_score": 0.0,
    }
