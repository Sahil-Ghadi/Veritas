import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

def get_model(temperature: float = 0.0):
    """
    Initialize and return the configured chat model.

    Supported providers:
    - ollama (default): uses OLLAMA_BASE_URL + LLM_MODEL
    - gemini: uses GEMINI_API_KEY + LLM_MODEL
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    model_name = os.getenv("LLM_MODEL", "qwen2.5:3b").strip()

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set in environment.")
        return ChatGoogleGenerativeAI(
            model=model_name or "gemini-2.5-flash",
            google_api_key=api_key,
            temperature=temperature,
        )

    # Default: local Ollama
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
    return ChatOllama(
        model=model_name or "qwen2.5:3b",
        base_url=ollama_base_url,
        temperature=temperature,
    )

# Default model instance
model = get_model()
