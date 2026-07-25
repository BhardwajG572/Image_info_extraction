"""
Calls the chosen Gemma model via the Google Gemini API (google-genai SDK).
One image + one prompt in, raw line-by-line text out.
Includes automatic retries for handling 429 Rate Limit errors.
"""
import base64
import time
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.config import AVAILABLE_MODELS, GEMINI_API_KEY
from backend.prompts import STRICT_EXTRACTION_SYSTEM_PROMPT, USER_EXTRACTION_INSTRUCTION

class ExtractionError(Exception):
    pass

def extract_from_image(
    model_key: str,
    image_b64: str,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> dict:
    """
    Sends base64 image and OCR extraction prompt to Gemma via Google GenAI SDK.
    Returns plain text lines inside a safe dictionary wrapper.
    """
    if model_key not in AVAILABLE_MODELS:
        raise ExtractionError(f"Unknown model key: {model_key}")

    model_cfg = AVAILABLE_MODELS[model_key]
    model_id = model_cfg["model_id"]

    try:
        # Initialize Google GenAI client
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Decode base64 image string into raw bytes
        image_bytes = base64.b64decode(image_b64)
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png",
        )

        # Configuration for plain-text generation
        config = types.GenerateContentConfig(
            system_instruction=STRICT_EXTRACTION_SYSTEM_PROMPT,
            temperature=temperature,
            max_output_tokens=max_tokens,
            # Removed response_mime_type="application/json" to allow plain text
        )

        # --- RETRY LOGIC FOR RATE LIMITS (429) ---
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=[image_part, USER_EXTRACTION_INSTRUCTION],
                    config=config,
                )
                break
            except APIError as api_err:
                if attempt == max_retries - 1:
                    raise api_err
                sleep_time = 2 ** attempt
                print(f"--- API RATE LIMIT (Attempt {attempt + 1}/{max_retries}) --- | Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

        raw_text = (response.text or "").strip()
        
        # Split text into clean individual lines
        extracted_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        return {
            "model_used": model_key,
            "model_id": model_id,
            "raw_response": raw_text,
            # Formatted into a dictionary wrapper to keep API contract stable
            "parsed": {
                "extracted_lines": extracted_lines,
                "raw_text_seen": raw_text,
            },
        }

    except Exception as exc:
        print(f"--- GEMINI API EXCEPTION ---\n{exc}")
        raise ExtractionError(f"Inference call failed for {model_key}: {exc}") from exc