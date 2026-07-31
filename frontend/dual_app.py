"""
Dual-Side Tire Inspection Pipeline - Streamlit dashboard.

Phase 1: Dual-side multi-image upload (Top Side + Bottom Side) + thumbnail galleries
Phase 2: Every uploaded image is STRICTLY force-hflipped immediately and shown in
         preprocessed galleries (Top & Bottom) - these are sent to the LLM
Phase 3: Extraction - preprocessed (flipped) images from both sides are sent to Gemma
Phase 4: Results grid categorized by Top Side and Bottom Side
Phase 5: Automatic deterministic (non-LLM) master summary synthesizing all extractions

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

# Ensure the backend module can be found
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL, BACKEND_URL, CANONICAL_FIELD_ORDER
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


st.title("🛞 Dual-Side Tire Inspection Pipeline")
st.caption(
    "Dual Upload (Top & Bottom Sides) → strictly preprocess (hflip) → extract (Gemma) "
    "→ deterministic master merge. No hallucinated summaries."
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
            if f.name in existing_names:
                continue
            
            b64 = base64.b64encode(f.read()).decode("utf-8")
            image_id = str(uuid.uuid4())[:8]

            st.session_state["raw_top_images"].append(
                {"image_id": image_id, "filename": f.name, "b64": b64, "side": "Top"}
            )
            flipped_b64 = hflip_b64(b64)
            st.session_state["preprocessed_top_images"].append(
                {"image_id": image_id, "filename": f.name, "b64": flipped_b64, "side": "Top"}
            )

    if st.session_state["raw_top_images"]:
        st.write(f"**{len(st.session_state['raw_top_images'])} Top image(s)**")
        clicked_top = render_image_grid(
            st.session_state["raw_top_images"], key_prefix="raw_top", columns=3
        )
        if clicked_top:
            _preview_dialog(st.session_state["raw_top_images"], clicked_top)

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
            if f.name in existing_names:
                continue
            
            b64 = base64.b64encode(f.read()).decode("utf-8")
            image_id = str(uuid.uuid4())[:8]

            st.session_state["raw_bottom_images"].append(
                {"image_id": image_id, "filename": f.name, "b64": b64, "side": "Bottom"}
            )
            flipped_b64 = hflip_b64(b64)
            st.session_state["preprocessed_bottom_images"].append(
                {"image_id": image_id, "filename": f.name, "b64": flipped_b64, "side": "Bottom"}
            )

    if st.session_state["raw_bottom_images"]:
        st.write(f"**{len(st.session_state['raw_bottom_images'])} Bottom image(s)**")
        clicked_bottom = render_image_grid(
            st.session_state["raw_bottom_images"], key_prefix="raw_bottom", columns=3
        )
        if clicked_bottom:
            _preview_dialog(st.session_state["raw_bottom_images"], clicked_bottom)

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
            clicked_pre_top = render_image_grid(
                st.session_state["preprocessed_top_images"], key_prefix="pre_top", columns=3
            )
            if clicked_pre_top:
                _preview_dialog(st.session_state["preprocessed_top_images"], clicked_pre_top)
        else:
            st.caption("No top side images.")

    with p_bottom_col:
        st.subheader("Preprocessed Bottom Side")
        if st.session_state["preprocessed_bottom_images"]:
            clicked_pre_bottom = render_image_grid(
                st.session_state["preprocessed_bottom_images"], key_prefix="pre_bottom", columns=3
            )
            if clicked_pre_bottom:
                _preview_dialog(st.session_state["preprocessed_bottom_images"], clicked_pre_bottom)
        else:
            st.caption("No bottom side images.")
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

        def _get_http_error_details(error: requests.HTTPError) -> str:
            response = error.response
            if response is None:
                return str(error)
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("message") or response.text
            except ValueError:
                detail = response.text
            return f"{response.status_code} {response.reason}: {detail}"

        def _send_batch_request(batch: list[dict]) -> dict:
            payload = {
                "images": [
                    {
                        "image_id": img["image_id"],
                        "image_b64": img["b64"], # STRICTLY flipped b64
                        "model_key": model_key,
                    }
                    for img in batch
                ]
            }

            retries = 3
            backoff = 1.0
            for attempt in range(1, retries + 1):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/extract_batch",
                        json=payload,
                        timeout=240,
                    )
                    resp.raise_for_status()
                    return {"success": True, "data": resp.json()}
                except requests.HTTPError as e:
                    if attempt == retries:
                        return {"success": False, "error": _get_http_error_details(e)}
                    time.sleep(backoff)
                    backoff *= 2
                except Exception as e:
                    if attempt == retries:
                        return {"success": False, "error": str(e)}
                    time.sleep(backoff)
                    backoff *= 2

        batch_size = 2
        max_workers = 3
        batches = [all_preprocessed[i : i + batch_size] for i in range(0, len(all_preprocessed), batch_size)]
        processed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(_send_batch_request, batch): batch for batch in batches
            }
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                result = future.result()
                if result["success"]:
                    data = result["data"]
                    for item in data.get("results", []):
                        if "error" in item:
                            st.session_state["extractions"][item["image_id"]] = {"error": item["error"]}
                        else:
                            st.session_state["extractions"][item["image_id"]] = item
                else:
                    err = result["error"]
                    for img in batch:
                        st.session_state["extractions"][img["image_id"]] = {"error": err}

                processed += len(batch)
                progress.progress(processed / total, text=f"Processed {processed}/{total} images")

        valid_extractions = [
            {"image_id": iid, "parsed": e["parsed"]}
            for iid, e in st.session_state["extractions"].items()
            if e and "parsed" in e
        ]
        
        if valid_extractions:
            progress.progress(1.0, text="Merging results...")
            try:
                merge_resp = requests.post(
                    f"{BACKEND_URL}/merge",
                    json={"extractions": valid_extractions},
                    timeout=60,
                )
                merge_resp.raise_for_status()
                st.session_state["merge_result"] = merge_resp.json()
            except requests.HTTPError as e:
                st.session_state["merge_result"] = None
                st.error(f"Merge failed: {_get_http_error_details(e)}")
            except Exception as e:
                st.session_state["merge_result"] = None
                st.error(f"Merge failed: {e}")

        progress.empty()
        st.rerun()
else:
    st.info("Upload images first.")

st.divider()

# --------------------------------------------------------------------------
# Phase 4: Results grid (Categorized by Side)
# --------------------------------------------------------------------------
st.header("4. Results")

if st.session_state["extractions"]:
    def _render_extraction_cards(images_list: list[dict]):
        if not images_list:
            st.caption("No images in this category.")
            return
        cols = st.columns(min(len(images_list), 3))
        for idx, img in enumerate(images_list):
            extraction = st.session_state["extractions"].get(img["image_id"])
            raw_img = _find_image(all_raw, img["image_id"])
            
            with cols[idx % min(len(images_list), 3)]:
                with st.container(border=True):
                    st.markdown(f"**[{img['side']} Side] {img['filename']}**")
                    
                    if extraction is None:
                        st.caption("Not yet processed.")
                        continue
                    if "error" in extraction:
                        st.error(f"Extraction Error: {extraction['error']}")
                        continue

                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Original")
                        if raw_img:
                            st.image(f"data:image/png;base64,{raw_img['b64']}", use_container_width=True)
                    with c2:
                        st.caption("Preprocessed (Flipped)")
                        st.image(f"data:image/png;base64,{img['b64']}", use_container_width=True)

                    st.json(extraction.get("parsed", {}), expanded=False)

                    parsed = extraction.get("parsed", {})
                    if "extracted_text" in parsed and parsed["extracted_text"]:
                        st.caption("Extracted Text Lines:")
                        for line in parsed["extracted_text"]:
                            st.text(line)

    st.subheader("⬆️ Top Side Results")
    _render_extraction_cards(st.session_state["preprocessed_top_images"])
    
    st.markdown("---")
    
    st.subheader("⬇️ Bottom Side Results")
    _render_extraction_cards(st.session_state["preprocessed_bottom_images"])
else:
    st.info("Run extraction above to see results.")

st.divider()

# --------------------------------------------------------------------------
# Phase 5: Master summary
# --------------------------------------------------------------------------
st.header("5. Deterministic Master Summary")

if st.session_state["merge_result"]:
    result = st.session_state["merge_result"]

    if result.get("warnings"):
        for w in result["warnings"]:
            st.error(w)
    else:
        st.success("All fields agreed across all uploaded images - no discrepancies.")

    st.subheader("Master Record (Top + Bottom Synthesized)")
    rows = []
    master_rec = result.get("master_record", {})
    field_rep = result.get("field_report", {})
    
    for field in CANONICAL_FIELD_ORDER:
        if field not in master_rec:
            continue
            
        status = field_rep.get(field, {}).get("status", "not_found")
        value = master_rec[field]
        
        rows.append(
            {
                "Field": field,
                "Value": value if value is not None else "—",
                "Status": status,
            }
        )
    st.table(rows)
else:
    st.info("Run extraction above to generate the summary.")