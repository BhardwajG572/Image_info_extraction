"""
Central configuration: environment secrets + the model registry.
Nothing in the app should hardcode a model id or token outside this file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Gemini API key - used to call Gemma models via the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Add it to your .env file "
        "(get one at https://aistudio.google.com/apikey)."
    )

# Gemma 4 models, served via the Gemini API (multimodal, image input supported)
AVAILABLE_MODELS = {
    "Google Gemma 4 (31B-It)": {"model_id": "gemma-4-31b-it"},
    "Google Gemma 4 (26B-A4B-It)": {"model_id": "gemma-4-26b-a4b-it"},
    "Google Gemma 4 (12B-It)": {"model_id": "gemma-4-12b-it"},
}

DEFAULT_MODEL = "Google Gemma 4 (31B-It)"

# Canonical field order for summary table rendering
CANONICAL_FIELD_ORDER = [
    "Brand",
    "Size",
    "DOT",
    "Load_Index",
    "Speed_Rating",
    "Plies",
    "Manufacture_Date",
    "Tread_Pattern",
    "Country_of_Origin",
    "Max_Pressure",
    "Raw_Notes",
]

# Backend host/port used by the Streamlit frontend to reach FastAPI.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")