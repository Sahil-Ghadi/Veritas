import asyncio
import os
from urllib.parse import urlparse
from collections import Counter

from tavily import AsyncTavilyClient


def _get_tavily() -> AsyncTavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY not set.")
    return AsyncTavilyClient(api_key=api_key)


async def search(query: str, max_results: int = 4) -> list[dict]:
    """Run a single Tavily search query and return raw result list."""
    client = _get_tavily()
    try:
        resp = await client.search(
            query=query,
            max_results=max_results,
            include_raw_content=True,
        )
        return resp.get("results", [])
    except Exception as e:
        print(f"[Search error] {query}: {e}")
        return []

# Keep private alias for internal use within this module
_search = search


async def adversarial_search(
    confirming_query: str,
    contradicting_query: str,
    max_results_each: int = 3,
) -> dict:
    """
    Run confirming + contradicting searches in parallel.
    Tag every result with its stance.
    Return:
        {
          "tagged_results": [...],
          "echo_chamber_detected": bool,
          "no_contradiction_found": bool,
        }
    """
    confirming, contradicting = await asyncio.gather(
        _search(confirming_query, max_results_each),
        _search(contradicting_query, max_results_each),
    )

    def tag_and_dedupe(items: list[dict], stance: str) -> list[dict]:
        seen_urls = set()
        output = []
        for r in items:
            url = (r.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            output.append({"stance": stance, **r})
        return output

    tagged = tag_and_dedupe(confirming, "supports") + tag_and_dedupe(contradicting, "contradicts")

    # Source diversity analysis across all results
    domains = [
        urlparse(r.get("url", "")).netloc.replace("www.", "")
        for r in tagged
    ]
    unique_domains = set(domains)
    domain_counts = Counter(domains)
    most_common_count = domain_counts.most_common(1)[0][1] if domain_counts else 0

    echo_chamber = most_common_count >= 3 or len(unique_domains) < 3
    no_contradiction_found = len(contradicting) == 0

    return {
        "tagged_results": tagged,
        "echo_chamber_detected": echo_chamber,
        "no_contradiction_found": no_contradiction_found,
    }