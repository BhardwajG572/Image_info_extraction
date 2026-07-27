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
    try:
        return merge_extractions(req.extractions)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Merge failed: {exc}") from exc


class ExtractBatchRequest(BaseModel):
    images: list[ExtractRequest]


@app.post("/extract_batch")
def extract_batch(req: ExtractBatchRequest):
    results = []
    for im in req.images:
        try:
            res = extract_from_image(
                model_key=im.model_key,
                image_b64=im.image_b64,
                temperature=im.temperature,
            )
            results.append({"image_id": im.image_id, **res})
        except ExtractionError as exc:
            results.append({"image_id": im.image_id, "error": str(exc)})
    return {"results": results}