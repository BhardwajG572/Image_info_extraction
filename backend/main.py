"""
FastAPI backend for the Tire Inspection Pipeline.

Endpoints:
  POST /extract   single-image VLM extraction (Gemma via Gemini API,
                   also reports Detected_Orientation)
  POST /merge      deterministic multi-image merge (no LLM)
  GET  /models      list available models for the frontend dropdown
  GET  /health

Run with:  uv run uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL
from backend.services import extract_from_image, ExtractionError
from backend.deterministic_merge import merge_extractions

app = FastAPI(title="Tire Inspection Pipeline API", version="1.0.0")


class ExtractRequest(BaseModel):
    image_id: str
    image_b64: str
    model_key: str = DEFAULT_MODEL
    temperature: float = 0.1


class MergeRequest(BaseModel):
    extractions: list[dict]  # [{"image_id": ..., "parsed": {...}}, ...]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models")
def list_models():
    return {
        "default": DEFAULT_MODEL,
        "models": {k: {"model_id": v["model_id"]} for k, v in AVAILABLE_MODELS.items()},
    }


@app.post("/extract")
def extract(req: ExtractRequest):
    try:
        result = extract_from_image(
            model_key=req.model_key,
            image_b64=req.image_b64,
            temperature=req.temperature,
        )
    except ExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"image_id": req.image_id, **result}


@app.post("/merge")
def merge(req: MergeRequest):
    if not req.extractions:
        raise HTTPException(status_code=400, detail="No extractions provided to merge.")
    return merge_extractions(req.extractions)