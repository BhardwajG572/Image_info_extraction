
"""
Dual-Side Tire Inspection Pipeline - Streamlit dashboard.

Phase 1: Dual-side multi-image upload (Top Side + Bottom Side)
Phase 2: Preprocessed galleries (Strictly Flipped)
Phase 3: Extraction
Phase 4: Results grid categorized by Side
Phase 5: Specification Compliance Table

Run with:  uv run streamlit run frontend/dual_app.py
"""
import base64
import concurrent.futures
import time
import uuid
import sys
from pathlib import Path

import requests
import streamlit as st
import pandas as pd

# Ensure the backend module can be found
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL, BACKEND_URL
from backend.image_pipeline import hflip_b64
from frontend.components import zoom_pan_viewer, render_image_grid

st.set_page_config(page_title="Dual Tire Inspection Pipeline", layout="wide")


def _init_state():
    defaults = {
        "raw_top_images": [],          # [{image_id, filename, b64, side: "Top"}]
        "preprocessed_top_images": [], # [{image_id, filename, b64, side: "Top"}]
        "raw_bottom_images": [],       # [{image_id, filename, b64, side: "Bottom"}]
        "preprocessed_bottom_images": [], # [{image_id, filename, b64, side: "Bottom"}]
        "extractions": {},             # image_id -> {parsed, model_used, ...}
        "merge_result": None,
        "preview_target": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

def _find_image(images: list[dict], image_id: str) -> dict | None:
    return next((i for i in images if i["image_id"] == image_id), None)

def _get_all_raw_images() -> list[dict]:
    return st.session_state["raw_top_images"] + st.session_state["raw_bottom_images"]

def _get_all_preprocessed_images() -> list[dict]:
    return st.session_state["preprocessed_top_images"] + st.session_state["preprocessed_bottom_images"]

@st.dialog("Image Preview", width="large")
def _preview_dialog(images: list[dict], image_id: str):
    img = _find_image(images, image_id)
    if img is None:
        st.error("Image not found.")
        return
    st.caption(f"{img.get('side', '')} Side: {img['filename']}")
    zoom_pan_viewer(img["b64"], height=560)
    if st.button("Close"):
        st.session_state["preview_target"] = None
        st.rerun()

st.title("🛞 Dual-Side Tire Compliance Pipeline")
st.caption(
    "Dual Upload (Top & Bottom) → strictly preprocess (hflip) → extract (Gemma) "
    "→ cross-reference with Ground Truth SKU Specs."
)

# --------------------------------------------------------------------------
# Phase 1: Dual Uploads (Top & Bottom Sides)
# --------------------------------------------------------------------------
st.header("1. Upload Tire Images")

col_top, col_bottom = st.columns(2)

with col_top:
    st.subheader("⬆️ Top Side Upload")
    uploaded_top_files = st.file_uploader(
        "Upload top-side tire images",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
        accept_multiple_files=True,
        key="top_uploader"
    )

    if uploaded_top_files:
        existing_names = {i["filename"] for i in st.session_state["raw_top_images"]}
        for f in uploaded_top_files:
            if f.name in existing_names: continue
            b64 = base64.b64encode(f.read()).decode("utf-8")
            image_id = str(uuid.uuid4())[:8]
            st.session_state["raw_top_images"].append({"image_id": image_id, "filename": f.name, "b64": b64, "side": "Top"})
            flipped_b64 = hflip_b64(b64)
            st.session_state["preprocessed_top_images"].append({"image_id": image_id, "filename": f.name, "b64": flipped_b64, "side": "Top"})

    if st.session_state["raw_top_images"]:
        clicked_top = render_image_grid(st.session_state["raw_top_images"], key_prefix="raw_top", columns=3)
        if clicked_top: _preview_dialog(st.session_state["raw_top_images"], clicked_top)

with col_bottom:
    st.subheader("⬇️ Bottom Side Upload")
    uploaded_bottom_files = st.file_uploader(
        "Upload bottom-side tire images",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
        accept_multiple_files=True,
        key="bottom_uploader"
    )

    if uploaded_bottom_files:
        existing_names = {i["filename"] for i in st.session_state["raw_bottom_images"]}
        for f in uploaded_bottom_files:
            if f.name in existing_names: continue
            b64 = base64.b64encode(f.read()).decode("utf-8")
            image_id = str(uuid.uuid4())[:8]
            st.session_state["raw_bottom_images"].append({"image_id": image_id, "filename": f.name, "b64": b64, "side": "Bottom"})
            flipped_b64 = hflip_b64(b64)
            st.session_state["preprocessed_bottom_images"].append({"image_id": image_id, "filename": f.name, "b64": flipped_b64, "side": "Bottom"})

    if st.session_state["raw_bottom_images"]:
        clicked_bottom = render_image_grid(st.session_state["raw_bottom_images"], key_prefix="raw_bottom", columns=3)
        if clicked_bottom: _preview_dialog(st.session_state["raw_bottom_images"], clicked_bottom)

all_raw = _get_all_raw_images()
if all_raw:
    st.write("---")
    if st.button("🗑️ Clear all uploads"):
        st.session_state["raw_top_images"] = []
        st.session_state["preprocessed_top_images"] = []
        st.session_state["raw_bottom_images"] = []
        st.session_state["preprocessed_bottom_images"] = []
        st.session_state["extractions"] = {}
        st.session_state["merge_result"] = None
        st.rerun()
else:
    st.info("Upload at least one image in either Top or Bottom side to begin.")

st.divider()

# --------------------------------------------------------------------------
# Phase 2: Preprocessed gallery (Strictly Flipped Images)
# --------------------------------------------------------------------------
st.header("2. Preprocessed Images (Strictly Flipped)")

all_preprocessed = _get_all_preprocessed_images()

if all_preprocessed:
    p_top_col, p_bottom_col = st.columns(2)
    
    with p_top_col:
        st.subheader("Preprocessed Top Side")
        if st.session_state["preprocessed_top_images"]:
            clicked_pre_top = render_image_grid(st.session_state["preprocessed_top_images"], key_prefix="pre_top", columns=3)
            if clicked_pre_top: _preview_dialog(st.session_state["preprocessed_top_images"], clicked_pre_top)
    with p_bottom_col:
        st.subheader("Preprocessed Bottom Side")
        if st.session_state["preprocessed_bottom_images"]:
            clicked_pre_bottom = render_image_grid(st.session_state["preprocessed_bottom_images"], key_prefix="pre_bottom", columns=3)
            if clicked_pre_bottom: _preview_dialog(st.session_state["preprocessed_bottom_images"], clicked_pre_bottom)
else:
    st.info("Upload images above to see the preprocessed versions here.")

st.divider()

# --------------------------------------------------------------------------
# Phase 3: Extraction (Sending the Flipped Images)
# --------------------------------------------------------------------------
st.header("3. Run Extraction")

model_key = st.selectbox(
    "Model",
    options=list(AVAILABLE_MODELS.keys()),
    index=list(AVAILABLE_MODELS.keys()).index(DEFAULT_MODEL),
)

if all_preprocessed:
    if st.button("🤖 Extract Data From All Images", type="primary"):
        total = len(all_preprocessed)
        progress = st.progress(0.0, text="Starting...")

        def _send_batch_request(batch: list[dict]) -> dict:
            payload = {
                "images": [
                    {"image_id": img["image_id"], "image_b64": img["b64"], "side": img["side"], "model_key": model_key}
                    for img in batch
                ]
            }
            try:
                resp = requests.post(f"{BACKEND_URL}/extract_batch", json=payload, timeout=240)
                resp.raise_for_status()
                return {"success": True, "data": resp.json()}
            except Exception as e:
                return {"success": False, "error": str(e)}

        batch_size = 2
        batches = [all_preprocessed[i : i + batch_size] for i in range(0, len(all_preprocessed), batch_size)]
        processed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {executor.submit(_send_batch_request, batch): batch for batch in batches}
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                result = future.result()
                if result["success"]:
                    for item in result["data"].get("results", []):
                        st.session_state["extractions"][item["image_id"]] = item
                else:
                    for img in batch:
                        st.session_state["extractions"][img["image_id"]] = {"error": result["error"]}

                processed += len(batch)
                progress.progress(processed / total, text=f"Processed {processed}/{total} images")

        valid_extractions = [
            {"image_id": iid, "side": _find_image(all_preprocessed, iid)["side"], "parsed": e["parsed"]}
            for iid, e in st.session_state["extractions"].items()
            if e and "parsed" in e
        ]
        
        if valid_extractions:
            progress.progress(1.0, text="Checking specifications...")
            try:
                merge_resp = requests.post(f"{BACKEND_URL}/merge", json={"extractions": valid_extractions}, timeout=60)
                merge_resp.raise_for_status()
                st.session_state["merge_result"] = merge_resp.json()
            except Exception as e:
                st.session_state["merge_result"] = None
                st.error(f"Compliance check failed: {e}")

        progress.empty()
        st.rerun()

st.divider()

# --------------------------------------------------------------------------
# Phase 4: Results grid (Categorized by Side)
# --------------------------------------------------------------------------
st.header("4. Raw Extractions")

if st.session_state["extractions"]:
    def _render_extraction_cards(images_list: list[dict]):
        if not images_list: return
        cols = st.columns(min(len(images_list), 3))
        for idx, img in enumerate(images_list):
            extraction = st.session_state["extractions"].get(img["image_id"])
            raw_img = _find_image(all_raw, img["image_id"])
            with cols[idx % min(len(images_list), 3)]:
                with st.container(border=True):
                    st.markdown(f"**[{img['side']}] {img['filename']}**")
                    if extraction and "parsed" in extraction:
                        st.json(extraction["parsed"], expanded=False)
                        if "extracted_text" in extraction["parsed"]:
                            with st.expander("Raw Text Lines"):
                                for line in extraction["parsed"]["extracted_text"]: st.text(line)

    st.subheader("⬆️ Top Side Results")
    _render_extraction_cards(st.session_state["preprocessed_top_images"])
    
    st.subheader("⬇️ Bottom Side Results")
    _render_extraction_cards(st.session_state["preprocessed_bottom_images"])

st.divider()

# --------------------------------------------------------------------------
# Phase 5: Master Specification Compliance Table
# --------------------------------------------------------------------------
st.header("5. Specification Compliance Table")

if st.session_state["merge_result"]:
    report = st.session_state["merge_result"].get("compliance_report", [])
    
    if report:
        # Convert to Pandas DataFrame for a clean deterministic table render
        df = pd.DataFrame(report)
        
        # Style the OK/NF statuses (Green for OK, Red for NF)
        def style_status(val):
            if val == 'OK':
                color = '#2ecc71' # Green
            elif val == 'NF':
                color = '#e74c3c' # Red
            else:
                color = 'inherit'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(
            df.style.map(style_status, subset=['Mould_Top', 'Mould_Bottom']), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("No data found to populate the compliance table.")
else:
    st.info("Run extraction above to generate the compliance report.")
