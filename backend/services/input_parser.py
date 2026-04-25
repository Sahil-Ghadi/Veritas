import httpx
import hashlib
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
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

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