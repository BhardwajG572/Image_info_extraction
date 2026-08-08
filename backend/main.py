"""
FastAPI backend for the Tire Inspection Pipeline.

Endpoints:
  POST /extract        single-image raw OCR-style extraction (Gemma via
                        Gemini API) -> {"extracted_text": [...]}
  POST /extract_batch   batch version of /extract
  POST /merge           classifies each image's raw extracted_text into
                        canonical fields (backend.field_mapper), then runs
                        the deterministic (non-LLM) merge across images
  GET  /models          list available models for the frontend dropdown
  GET  /health

Run with:  uv run uvicorn backend.main:app --reload --port 8000
"""
import json
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL, CANONICAL_FIELD_ORDER, SKU_SPECIFICATIONS
from backend.services import extract_from_image, ExtractionError
from backend.field_mapper import map_extraction_to_fields
from backend.deterministic_merge import merge_extractions
from backend.image_pipeline import hflip_b64

app = FastAPI(title="Tire Inspection Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    image_id: str
    image_b64: str
    model_key: str = DEFAULT_MODEL
    temperature: float = 0.1

from typing import Optional

class MergeRequest(BaseModel):
    extractions: list[dict]  # [{"image_id": ..., "parsed": {"extracted_text": [...]}}, ...]
    sku_specifications: Optional[dict] = None
    sku_name: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/models")
def list_models():
    return {
        "default": DEFAULT_MODEL,
        "models": {k: {"model_id": v["model_id"]} for k, v in AVAILABLE_MODELS.items()},
    }

DYNAMIC_SKUS_FILE = "backend/dynamic_skus.json"

@app.get("/skus")
def get_skus():
    if not os.path.exists(DYNAMIC_SKUS_FILE):
        return {"skus": {}}
    try:
        with open(DYNAMIC_SKUS_FILE, "r", encoding="utf-8") as f:
            skus = json.load(f)
        return {"skus": skus}
    except Exception as e:
        print(f"Failed to read skus: {e}")
        return {"skus": {}}

class SaveSkuRequest(BaseModel):
    name: str
    metadata: dict
    parameters: list

@app.post("/skus")
def save_sku(req: SaveSkuRequest):
    skus = {}
    if os.path.exists(DYNAMIC_SKUS_FILE):
        try:
            with open(DYNAMIC_SKUS_FILE, "r", encoding="utf-8") as f:
                skus = json.load(f)
        except Exception:
            pass
            
    skus[req.name] = {
        "metadata": req.metadata,
        "parameters": req.parameters
    }
    
    with open(DYNAMIC_SKUS_FILE, "w", encoding="utf-8") as f:
        json.dump(skus, f, indent=4)
        
    return {"status": "ok", "name": req.name}

@app.get("/fields")
def list_fields():
    return {
        "canonical_fields": CANONICAL_FIELD_ORDER,
        "default_specs": SKU_SPECIFICATIONS,
        "available_skus": {
            "APOLLO APTERRA CROSS 215/60 R17": SKU_SPECIFICATIONS
        }
    }

@app.get("/history")
def get_history():
    if not os.path.exists("history.json"):
        return {"history": []}
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
        return {"history": history}
    except Exception as e:
        print(f"Failed to read history: {e}")
        return {"history": []}

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
        with open("all_extractions.json", "w", encoding="utf-8") as f:
            json.dump(req.extractions, f, indent=4)
        print("--- Saved all extractions to all_extractions.json ---")
    except Exception as e:
        print(f"Failed to save extractions to JSON: {e}")

    mapped_extractions = []
    unmatched_by_image = {}
    conflicts_by_image = {}

    for item in req.extractions:
        image_id = item.get("image_id", "unknown")
        raw_parsed = item.get("parsed", {}) or {}
        extracted_text = raw_parsed.get("extracted_text", []) or []

        field_dict = map_extraction_to_fields(extracted_text, sku_specifications=req.sku_specifications)

        # Pull the visibility metadata out before handing fields to the
        # merge step, so it doesn't get treated as a mergeable field itself.
        unmatched = field_dict.pop("_unmatched", None)
        conflicts = field_dict.pop("_conflicts", None)
        if unmatched:
            unmatched_by_image[image_id] = unmatched
        if conflicts:
            conflicts_by_image[image_id] = conflicts

        side = item.get("side", "Unknown")
        mapped_extractions.append({"image_id": image_id, "side": side, "parsed": field_dict})

    try:
        result = merge_extractions(mapped_extractions, sku_specifications=req.sku_specifications)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Merge failed: {exc}") from exc

    # Surface classification-time visibility info alongside the merge
    # result, without polluting master_record/field_report with it.
    result["unmatched_text_by_image"] = unmatched_by_image
    result["field_conflicts_by_image"] = conflicts_by_image

    # Save to history.json
    try:
        history_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "sku_specifications": req.sku_specifications,
            "sku_name": req.sku_name,
            "result": result
        }
        
        history = []
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        history.insert(0, history_entry) # Put newest first
        
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
        print("--- Saved merge result to history.json ---")
    except Exception as e:
        print(f"Failed to append to history.json: {e}")

    return result

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
            print(f"\n--- Extracted Data for Image {im.image_id} ---")
            print(json.dumps(res, indent=2))
            results.append({"image_id": im.image_id, **res})
        except ExtractionError as exc:
            results.append({"image_id": im.image_id, "error": str(exc)})
    return {"results": results}

class PreprocessRequestItem(BaseModel):
    image_id: str
    image_b64: str
    side: str

class PreprocessRequest(BaseModel):
    images: list[PreprocessRequestItem]

@app.post("/preprocess")
def preprocess(req: PreprocessRequest):
    results = []
    for im in req.images:
        try:
            processed_b64 = hflip_b64(im.image_b64)
            results.append({
                "image_id": im.image_id,
                "image_b64": processed_b64,
                "side": im.side
            })
        except Exception as e:
            results.append({
                "image_id": im.image_id,
                "error": str(e)
            })
    return {"results": results}