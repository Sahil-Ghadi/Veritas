import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_model(temperature: float = 0.0):
    """
    Initialize and return the configured chat model.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set in environment.")
    
    model_name = "gemini-2.5-flash"
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
    )

# Default model instance
model = get_model()
