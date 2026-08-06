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
    "Size designation",
    "Load index",
    "Speed index",
    "Brand",
    "Productline",
    "Tubetype/tubeless",
    "Load index class",
    "DOT marking",
    "DOT Plant Code",
    "DOT Manufacturers Code",
    "Utqg Marking",
    "Temperature",
    "Traction",
    "Tread wear",
    "Tread Wear Indicator (TWI)",
    "ISI Marking",
    "E-appr. code (S/W/R)",
    "E-approval code",
    "Inmetro 200 engraved",
    "Indonesia certificate (SNI)",
    "Philipinnes certificate (PBS)",
    "AIS Marking",
    "China certificate (CCC)",
    "Winter indication",
    "M+S Marking",
    "Directional",
    "Inner side",
    "Outer side",
    "EV Ready",
    "Sustainability",
    "Giugiaro Design",
    "Adventure comfort",
    "OE SPECIFIC MARKING",
    "Made in",
    "Safety warning",
    "Plies tread",
    "Plies sidewall",
    "Maximum Inflation Pressure (KPA)",
    "Maximum Inflation Pressure (PSI)",
    "Maximum Load (KG)",
    "Maximum Load (LBS)",
    "Maximum Load Single (LBS)",
    "Maximum Load Single (KG)",
    "Maximum Load Dual (LBS)",
    "Maximum Load Dual (KG)",
    "Maximum Inflation Pressure Single (PSI)",
    "Maximum Inflation Pressure Single (KPA)",
    "Maximum Inflation Pressure Dual (PSI)",
    "Maximum Inflation Pressure Dual (KPA)",
    "Load range",
    "Ply rating",
    "p_max testing",
    "Mould Drawing No",
    "Tyre Mould Segment",
    "Tyre Side Plate Id",
    "FITMENT",
    "Manufacture date code",
    "Mold reference number",
    "Cure Tyre Identification"
]

# --- SPECIFICATION COMPLIANCE VARIABLES ---
SKU_SPECIFICATIONS = {
    "Size designation": "215/60 R17",
    "Load index": "96",
    "Speed index": "H",
    "Brand": "APOLLO",
    "Productline": "APTERRA CROSS",
    "Tubetype/tubeless": "RADIAL TUBELESS",
    "Load index class": "",
    "DOT marking": "DOT",
    "DOT Plant Code": "1P0",
    "DOT Manufacturers Code": "KTC305",
    "Utqg Marking": "", 
    "Temperature": "TEMPERATURE A", 
    "Traction": "TRACTION A",       
    "Tread wear": "TREADWEAR 460",  
    "Tread Wear Indicator (TWI)": "YES",
    "ISI Marking": "IS:15633 CM/L-3382863",
    "E-appr. code (S/W/R)": "E4 0211093 S2WR2",
    "E-approval code": "E4 02119426",
    "Inmetro 200 engraved": "",
    "Indonesia certificate (SNI)": "",
    "Philipinnes certificate (PBS)": "",
    "AIS Marking": "",
    "China certificate (CCC)": "",
    "Winter indication": "",
    "M+S Marking": "M+S",
    "Directional": "",
    "Inner side": "",
    "Outer side": "",
    "EV Ready": "",
    "Sustainability": "",
    "Giugiaro Design": "",
    "Adventure comfort": "",
    "OE SPECIFIC MARKING": "",
    "Made in": "MADE IN INDIA",
    "Safety warning": "Warning",
    "Plies tread": "1PE+2STL+1NYL,TREAD: 1 POLYESTER + 2 STEEL + 1 NYLON",
    "Plies sidewall": "2 POLYESTER,SIDE WALL:2 POLYESTER",
    "Maximum Inflation Pressure (KPA)": "350",
    "Maximum Inflation Pressure (PSI)": "51",
    "Maximum Load (KG)": "710",
    "Maximum Load (LBS)": "1565",
    "Maximum Load Single (LBS)": "",
    "Maximum Load Single (KG)": "",
    "Maximum Load Dual (LBS)": "",
    "Maximum Load Dual (KG)": "",
    "Maximum Inflation Pressure Single (PSI)": "",
    "Maximum Inflation Pressure Single (KPA)": "",
    "Maximum Inflation Pressure Dual (PSI)": "",
    "Maximum Inflation Pressure Dual (KPA)": "",
    "Load range": "",
    "Ply rating": "",
    "p_max testing": "",
    "Mould Drawing No": "",
    "Tyre Mould Segment": "",
    "Tyre Side Plate Id": "",
    "FITMENT": "",
    "Manufacture date code": "WWYY",
    "Mold reference number": "B8524-**",
    "Cure Tyre Identification": "WHITE"
}

# Defines strictly which side a marking MUST appear on to be marked "OK".
SIDE_SPECIFIC_RULES = {
    "Safety warning": "Top",
    "ISI Marking": "Bottom"
}

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
