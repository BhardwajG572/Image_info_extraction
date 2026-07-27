"""
Calls the chosen model via the Google Gemini API (google-genai SDK).
One image + one prompt in, strict JSON dictionary out for the deterministic merge.
Includes automatic retries for handling 429 Rate Limit errors and robust JSON repair.
"""
import base64
import json
import re
import time
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.config import AVAILABLE_MODELS, GEMINI_API_KEY
from backend.prompts import STRICT_EXTRACTION_SYSTEM_PROMPT, USER_EXTRACTION_INSTRUCTION

class ExtractionError(Exception):
    pass

def _clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
    text = re.sub(r"```$", "", text, flags=re.I).strip()
    return text


def _strip_non_json_wrappers(text: str) -> str:
    first = min([pos for pos in (text.find("{"), text.find("[")) if pos != -1], default=-1)
    last = max(text.rfind("}"), text.rfind("]"))
    if first != -1 and last != -1 and last > first:
        return text[first : last + 1]
    return text


def _remove_inline_comments(text: str) -> str:
    result = []
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            result.append(ch)
            escape = False
            continue
        if ch == "\\":
            result.append(ch)
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue
        if not in_string and ch == "#":
            # drop the rest of the line outside a string
            while i + 1 < len(text) and text[i + 1] not in "\r\n":
                i += 1
            continue
        result.append(ch)
    return "".join(result)


def _remove_trailing_commas(text: str) -> str:
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def _balance_brackets_and_quotes(text: str) -> str:
    if text.count('"') % 2 == 1:
        text = text + '"'
    curly_open = text.count("{")
    curly_close = text.count("}")
    if curly_open > curly_close:
        text += "}" * (curly_open - curly_close)
    square_open = text.count("[")
    square_close = text.count("]")
    if square_open > square_close:
        text += "]" * (square_open - square_close)
    return text


def _repair_json_text(raw_text: str) -> str:
    text = _clean_json_text(raw_text)
    text = _strip_non_json_wrappers(text)
    text = _remove_inline_comments(text)
    text = _remove_trailing_commas(text)
    text = _balance_brackets_and_quotes(text)
    return text


def _repair_with_model(raw_text: str, model_id: str, temperature: float = 0.1) -> str:
    repair_instruction = (
        "The previous extraction output is malformed JSON. "
        "Please return valid JSON only, with the same field names and values as the broken output. "
        "Do not add any explanation or markdown fencing."
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        system_instruction=repair_instruction,
        temperature=temperature,
        max_output_tokens=1024,
        response_mime_type="application/json",
    )

    response = client.models.generate_content(
        model=model_id,
        contents=[raw_text],
        config=config,
    )
    return response.text or ""


def extract_from_image(
    model_key: str,
    image_b64: str,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> dict:
    if model_key not in AVAILABLE_MODELS:
        raise ExtractionError(f"Unknown model key: {model_key}")

    model_cfg = AVAILABLE_MODELS[model_key]
    model_id = model_cfg["model_id"]

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        image_bytes = base64.b64decode(image_b64)
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png",
        )

        config = types.GenerateContentConfig(
            system_instruction=STRICT_EXTRACTION_SYSTEM_PROMPT,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )

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

        raw_text = response.text or ""
        cleaned_text = _clean_json_text(raw_text)

        # --- FIX: Handle completely blank responses gracefully before trying to parse/repair ---
        if not cleaned_text.strip():
            parsed_dict = {}
        else:
            try:
                parsed_dict = json.loads(cleaned_text)
            except json.JSONDecodeError as decode_err:
                repaired_text = _repair_json_text(raw_text)
                try:
                    parsed_dict = json.loads(repaired_text)
                except json.JSONDecodeError:
                    try:
                        repaired_raw = _repair_with_model(raw_text, model_id, temperature)
                        repaired_raw = _clean_json_text(repaired_raw)
                        parsed_dict = json.loads(repaired_raw)
                    except Exception as final_err:
                        error_msg = (
                            f"Model failed to return valid JSON. Error: {decode_err} | "
                            f"Raw output: {raw_text[:400]}"
                        )
                        print(f"--- JSON PARSE ERROR ---\n{error_msg}")
                        raise ExtractionError(error_msg) from final_err

        return {
            "model_used": model_key,
            "model_id": model_id,
            "raw_response": raw_text,
            "parsed": parsed_dict,
        }

    except Exception as exc:
        print(f"--- GEMINI API EXCEPTION ---\n{exc}")
        raise ExtractionError(f"Inference call failed for {model_key}: {exc}") from exc