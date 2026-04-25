import asyncio
import os
from urllib.parse import urlparse
from collections import Counter
from functools import lru_cache

from tavily import AsyncTavilyClient

# ── Singleton client ────────────────────────────────────────────────────────
# Creating a new AsyncTavilyClient on every search call adds unnecessary
# connection-setup overhead. We build it once and reuse it.
@lru_cache(maxsize=1)
def _get_tavily() -> AsyncTavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY not set.")
    return AsyncTavilyClient(api_key=api_key)


_SEARCH_TIMEOUT_S = 15  # hard cap per query — prevents pipeline stalls


async def search(query: str, max_results: int = 4) -> list[dict]:
    """
    Run a single Tavily search query and return raw result list.

    Performance notes:
      - search_depth="basic" skips Tavily's deep-crawl pass (~40 % faster).
      - include_raw_content is intentionally omitted (defaults to False);
        fetching full page bodies was the single largest latency driver.
        Titles + snippets are sufficient for alignment/judge.
      - A hard asyncio timeout prevents one slow DNS/network hop from
        blocking the whole pipeline.
    """
    client = _get_tavily()
    try:
        resp = await asyncio.wait_for(
            client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
            ),
            timeout=_SEARCH_TIMEOUT_S,
        )
        return resp.get("results", [])
    except asyncio.TimeoutError:
        print(f"[Search timeout] query took >{_SEARCH_TIMEOUT_S}s — returning empty: {query[:80]}")
        return []
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
    # Skip the second query if it's identical to the first (saves one API call)
    if confirming_query.strip().lower() == contradicting_query.strip().lower():
        confirming_raw = await _search(confirming_query, max_results_each)
        contradicting_raw: list[dict] = []
    else:
        confirming_raw, contradicting_raw = await asyncio.gather(
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

    tagged = tag_and_dedupe(confirming_raw, "supports") + tag_and_dedupe(contradicting_raw, "contradicts")

    # Source diversity analysis across all results
    domains = [
        urlparse(r.get("url", "")).netloc.replace("www.", "")
        for r in tagged
    ]
    unique_domains = set(domains)
    domain_counts = Counter(domains)
    most_common_count = domain_counts.most_common(1)[0][1] if domain_counts else 0

    echo_chamber = most_common_count >= 3 or len(unique_domains) < 3
    no_contradiction_found = len(contradicting_raw) == 0

    return {
        "tagged_results": tagged,
        "echo_chamber_detected": echo_chamber,
        "no_contradiction_found": no_contradiction_found,
    }