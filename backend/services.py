"""
backend/services.py

Calls the chosen model via the Google Gemini API (google-genai SDK).
One image + one prompt in, {"extracted_text": [...]} raw JSON out per image.
This is the raw-extraction pass only — mapping into canonical fields and
merging across images happens later in a separate deterministic step.

This is the single canonical extraction module — backend/main.py imports
`extract_from_image` and `ExtractionError` from here. (Previously this logic
was duplicated across an unnamed file and backend/gemini_client.py; those
have been consolidated into this one file. Delete backend/gemini_client.py.)

Includes:
  - A single module-level genai.Client (created once, not per-call)
  - Automatic retries for handling 429 Rate Limit errors
  - A multi-step, non-LLM JSON repair chain, with a model-based repair
    call as the last resort
"""
import base64
import json
import re
import time
from typing import Any, Dict

from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.config import AVAILABLE_MODELS, GEMINI_API_KEY
from backend.prompts import OCR_JSON_PROMPT, USER_OCR_INSTRUCTION


class ExtractionError(Exception):
    pass


# Initialize the client once at module level (reused across all calls,
# instead of constructing a new genai.Client per request).
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Schema-constrained output for the raw per-image OCR-style pass.
#
# IMPORTANT: the Gemini API has two DIFFERENT, MUTUALLY EXCLUSIVE schema
# mechanisms:
#   - response_schema      -> OpenAPI-subset format, UPPERCASE types
#                              ("OBJECT", "STRING", ...)
#   - response_json_schema -> standard JSON Schema, lowercase types
#                              ("object", "string", ...)
# Only one may be set at a time (setting response_json_schema requires
# response_schema to be omitted). Gemma 4 has been reported to not honor
# response_schema reliably — it keeps "thinking" and burns the output-token
# budget regardless — but does honor response_json_schema. We use the latter.
RAW_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "extracted_text": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["extracted_text"],
}


# --------------------------------------------------------------------------
# JSON cleanup / repair chain (non-LLM, cheap, tried before any model call)
# --------------------------------------------------------------------------
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
    i = 0
    while i < len(text):
        ch = text[i]
        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue
        if ch == "\\":
            result.append(ch)
            escape = True
            i += 1
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue
        if not in_string and ch == "#":
            while i + 1 < len(text) and text[i + 1] not in "\r\n":
                i += 1
            i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


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
    """Last-resort repair: ask the model to re-emit valid JSON. Reuses the
    module-level client instead of constructing a new one."""
    repair_instruction = (
        "The previous extraction output is malformed JSON. "
        "Please return valid JSON only, with the same field names and values as the broken output. "
        "Do not add any explanation or markdown fencing."
    )
    config = types.GenerateContentConfig(
        system_instruction=repair_instruction,
        temperature=temperature,
        max_output_tokens=2048,
        response_mime_type="application/json",
        response_json_schema=RAW_EXTRACTION_JSON_SCHEMA,
    )
    response = genai_client.models.generate_content(
        model=model_id,
        contents=[raw_text],
        config=config,
    )
    return response.text or ""


# --------------------------------------------------------------------------
# Main extraction entry point
# --------------------------------------------------------------------------
def extract_from_image(
    model_key: str,
    image_b64: str,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    if model_key not in AVAILABLE_MODELS:
        raise ExtractionError(f"Unknown model key: {model_key}")

    model_id = AVAILABLE_MODELS[model_key]["model_id"]

    try:
        image_bytes = base64.b64decode(image_b64)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        config = types.GenerateContentConfig(
            system_instruction=OCR_JSON_PROMPT,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_json_schema=RAW_EXTRACTION_JSON_SCHEMA,
            # NOTE: thinking_config/thinking_budget is REJECTED outright
            # (400 INVALID_ARGUMENT: "Thinking budget is not supported for
            # this model") for these Gemma model IDs — do not set it here.
            # response_json_schema alone is what suppresses the "thinking
            # first" behavior for Gemma 4.
        )

        max_retries = 3
        response = None
        # Only 429 (rate limit) and 5xx (transient server-side) are worth
        # retrying. A 400 INVALID_ARGUMENT (bad model id, unsupported
        # param, malformed schema, etc.) will fail identically on every
        # attempt — retrying it just burns 3x the latency for the same
        # error, so fail fast on those instead.
        RETRYABLE_CODES = {429, 500, 502, 503, 504}

        for attempt in range(max_retries):
            try:
                response = genai_client.models.generate_content(
                    model=model_id,
                    contents=[image_part, USER_OCR_INSTRUCTION],
                    config=config,
                )
                break
            except APIError as api_err:
                if api_err.code not in RETRYABLE_CODES or attempt == max_retries - 1:
                    raise api_err
                sleep_time = 2**attempt
                print(
                    f"--- API ERROR {api_err.code} (Attempt {attempt + 1}/{max_retries}) --- "
                    f"| Retrying in {sleep_time}s..."
                )
                time.sleep(sleep_time)

        raw_text = response.text or ""
        cleaned_text = _clean_json_text(raw_text)

        if not cleaned_text.strip():
            # An empty body is not automatically "nothing visible on the
            # tire" - it's very often MAX_TOKENS (thinking ate the budget)
            # or a safety block. Surface that instead of silently returning
            # an empty dict, which previously made every image look like a
            # clean-but-empty extraction with no visible error.
            finish_reason = None
            safety_info = None
            try:
                candidate = response.candidates[0] if response.candidates else None
                if candidate is not None:
                    finish_reason = getattr(candidate, "finish_reason", None)
                    safety_info = getattr(candidate, "safety_ratings", None)
            except Exception:
                pass
            raise ExtractionError(
                "Model returned an empty response body "
                f"(finish_reason={finish_reason}, safety_ratings={safety_info}). "
                "This usually means the thinking/reasoning tokens consumed the "
                "entire max_output_tokens budget before any JSON was written, "
                "or the response was blocked by a safety filter."
            )
        else:
            try:
                parsed_dict = json.loads(cleaned_text)
            except json.JSONDecodeError as decode_err:
                # Step 1: cheap, local, non-LLM repair chain
                repaired_text = _repair_json_text(raw_text)
                try:
                    parsed_dict = json.loads(repaired_text)
                except json.JSONDecodeError:
                    # Step 2: last resort, ask the model to re-emit valid JSON
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

    except ExtractionError:
        raise
    except Exception as exc:
        print(f"--- GEMINI API EXCEPTION ---\n{exc}")
        raise ExtractionError(f"Inference call failed for {model_key}: {exc}") from exc