# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Google Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Add it to your .env file "
        "(get one at https://aistudio.google.com/apikey)."
    )

# Model Registry
AVAILABLE_MODELS = {
    "Google Gemma 4 (31B-It)": {"model_id": "gemma-4-31b-it"},
    "Google Gemma 4 (26B-A4B-It)": {"model_id": "gemma-4-26b-a4b-it"},
    "Google Gemma 4 (12B-It)": {"model_id": "gemma-4-12b-it"},
}

DEFAULT_MODEL = "Google Gemma 4 (31B-It)"

# Canonical field order for summary table rendering
CANONICAL_FIELD_ORDER = [
    "BRAND", "MODEL", "SIZE", "MOULD", "LOAD_IDX", "SPEED", "DOT", 
    "DPC", "DMC", "PSI", "KPA", "LOAD_KG", "LOAD_LBS", "TYPE", 
    "SAFETY", "MARK", "TRAC", "TEMP", "TWEAR", "UTQG", "INDIA", 
    "P_TREAD", "SIDEWALL", "NOISE", "ECE", "ISI"
]

# --- SPECIFICATION COMPLIANCE VARIABLES ---
# All 26 canonical fields mapped to their Ground Truth Specifications
SKU_SPECIFICATIONS = {
    "BRAND": "APOLLO",
    "MODEL": "APTERRA CROSS",
    "SIZE": "215/60 R17",
    "MOULD": "B8524",
    "LOAD_IDX": "96",
    "SPEED": "H",
    "DOT": "DOT",
    "DPC": "1P0",
    "DMC": "KTC305",
    "PSI": "51",
    "KPA": "350",
    "LOAD_KG": "710",
    "LOAD_LBS": "1565",
    "TYPE": "RADIAL TUBELESS",
    "SAFETY": "Warning",
    "MARK": "M+S",
    "TRAC": "TRACTION A",
    "TEMP": "TEMPERATURE A",
    "TWEAR": "TREADWEAR 460",
    "UTQG": "",  # Empty as per specification
    "INDIA": "MADE IN INDIA",
    "P_TREAD": "TREAD: 1 POLYESTER + 2 STEEL + 1 NYLON",
    "SIDEWALL": "SIDE WALL:2 POLYESTER",
    "NOISE": "E4 0211093 S2WR2",
    "ECE": "E4 02119426",
    "ISI": "IS:15633 CM/L-3382863"
}

# Defines strictly which side a marking MUST appear on to be marked "OK".
SIDE_SPECIFIC_RULES = {
    "SAFETY": "Top",
    "ISI": "Bottom"
}

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
