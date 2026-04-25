from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_settings():
    return {
        "app_env": os.getenv("APP_ENV", "development"),
        "origins_list": os.getenv("ORIGINS_LIST", "*").split(","),
    }