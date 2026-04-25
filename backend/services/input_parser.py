import httpx
import hashlib
import asyncio
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage
from core.llm_client import model

async def fetch_url_text(url: str) -> str:
    """Fetch and extract clean text from a URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    timeout = httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)
    last_error: Exception | None = None
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        for attempt in range(3):
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                break
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as exc:
                last_error = exc
                if attempt == 2:
                    raise ValueError(
                        f"Could not fetch URL after retries ({type(exc).__name__}). "
                        "Please retry or use input_type='text'."
                    ) from exc
                await asyncio.sleep(0.6 * (attempt + 1))
            except httpx.HTTPStatusError as exc:
                raise ValueError(
                    f"URL returned HTTP {exc.response.status_code}. "
                    "Please verify the URL or use input_type='text'."
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == 2:
                    raise ValueError(
                        f"Could not fetch URL ({type(exc).__name__}). "
                        "Please retry or use input_type='text'."
                    ) from exc
                await asyncio.sleep(0.6 * (attempt + 1))
        else:
            # Safety fallback; should be unreachable due to raise/break above.
            if last_error is not None:
                raise ValueError(
                    f"Could not fetch URL ({type(last_error).__name__}). "
                    "Please retry or use input_type='text'."
                ) from last_error

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.body
    text = article.get_text(separator="\n", strip=True) if article else soup.get_text()
    
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

async def extract_text_from_image(base64_image: str, media_type: str = "image/jpeg") -> str:
    """Use vision LLM to extract text from a news screenshot."""
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "Extract ALL text from this news article screenshot exactly as written. Return only the extracted text."
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{base64_image}"}
            },
        ]
    )
    response = await model.ainvoke([message])
    return response.content

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()

async def parse_input(raw_input: str, input_type: str) -> dict:
    if input_type == "url":
        parsed_text = await fetch_url_text(raw_input)
    elif input_type == "image":
        parsed_text = await extract_text_from_image(raw_input)
    else:
        parsed_text = raw_input.strip()

    return {
        "parsed_text": parsed_text,
        "content_hash": compute_hash(parsed_text),
    }