import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_model(temperature: float = 0.0):
    """Initialize and return the Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set in environment.")

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", # User requested 2.5-flash
        google_api_key=api_key,
        temperature=temperature,
    )

# Default model instance
model = get_model()
