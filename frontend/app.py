"""
Tire Inspection Pipeline - Streamlit dashboard.

Phase 1: multi-image upload + thumbnail gallery
Phase 2: every uploaded image is force-hflipped immediately and shown in
         a preprocessed gallery - this is what actually gets sent to the LLM
Phase 3: extraction - the PREPROCESSED (flipped) image is what's sent to
         Gemma, never the raw upload
Phase 4: results grid (original / preprocessed / extracted JSON)
Phase 5: automatic deterministic (non-LLM) master summary

Run with:  uv run streamlit run frontend/app.py
"""
import base64
import concurrent.futures
import time
import uuid

import requests
import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL, BACKEND_URL, CANONICAL_FIELD_ORDER
from backend.image_pipeline import hflip_b64
from frontend.components import zoom_pan_viewer, render_image_grid

st.set_page_config(page_title="Tire Inspection Pipeline", layout="wide")


def _init_state():
    defaults = {
        "raw_images": [],          # [{image_id, filename, b64}]
        "preprocessed_images": [], # [{image_id, filename, b64}] - flipped
        "extractions": {},         # image_id -> {parsed, model_used, ...}
        "merge_result": None,
        "preview_target": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


def _find_image(images: list[dict], image_id: str) -> dict | None:
    return next((i for i in images if i["image_id"] == image_id), None)


@st.dialog("Image Preview", width="large")
def _preview_dialog(images: list[dict], image_id: str):
    img = _find_image(images, image_id)
    if img is None:
        st.error("Image not found.")
        return
    st.caption(img["filename"])
    zoom_pan_viewer(img["b64"], height=560)
    if st.button("Close"):
        st.session_state["preview_target"] = None
        st.rerun()


st.title("🛞 Tire Inspection Pipeline")
st.caption(
    "Upload → preprocess (hflip) → extract (Gemma, on the preprocessed "
    "image) → deterministic merge. No hallucinated summaries."
)

# --------------------------------------------------------------------------
# Phase 1: Upload
# --------------------------------------------------------------------------
st.header("1. Upload Tire Images")
uploaded_files = st.file_uploader(
    "Upload one or more tire images (multiple angles supported, any session)",
    type=["png", "jpg", "jpeg", "bmp", "webp"],
    accept_multiple_files=True,
)

if uploaded_files:
    existing_names = {i["filename"] for i in st.session_state["raw_images"]}
    for f in uploaded_files:
        if f.name in existing_names:
            continue
        b64 = base64.b64encode(f.read()).decode("utf-8")
        image_id = str(uuid.uuid4())[:8]

        st.session_state["raw_images"].append(
            {"image_id": image_id, "filename": f.name, "b64": b64}
        )
        # Preprocess immediately on upload - flip happens here, once,
        # and this is the exact image that will later go to the LLM.
        flipped_b64 = hflip_b64(b64)
        st.session_state["preprocessed_images"].append(
            {"image_id": image_id, "filename": f.name, "b64": flipped_b64}
        )

if st.session_state["raw_images"]:
    st.write(f"**{len(st.session_state['raw_images'])} image(s) uploaded**")
    clicked = render_image_grid(
        st.session_state["raw_images"], key_prefix="raw", columns=4
    )
    if clicked:
        _preview_dialog(st.session_state["raw_images"], clicked)

    if st.button("🗑️ Clear all uploads"):
        st.session_state["raw_images"] = []
        st.session_state["preprocessed_images"] = []
        st.session_state["extractions"] = {}
        st.session_state["merge_result"] = None
        st.rerun()
else:
    st.info("Upload at least one image to begin.")

st.divider()

# --------------------------------------------------------------------------
# Phase 2: Preprocessed gallery (visible before extraction runs)
# --------------------------------------------------------------------------
st.header("2. Preprocessed Images (Flipped)")

if st.session_state["preprocessed_images"]:
    st.caption("This is the exact image that will be sent to the LLM for extraction.")
    clicked_pre = render_image_grid(
        st.session_state["preprocessed_images"], key_prefix="pre", columns=4
    )
    if clicked_pre:
        _preview_dialog(st.session_state["preprocessed_images"], clicked_pre)
else:
    st.info("Upload images above to see the preprocessed versions here.")

st.divider()

# --------------------------------------------------------------------------
# Phase 3+4+5: Extraction + merge
# --------------------------------------------------------------------------
st.header("3. Run Extraction")

model_key = st.selectbox(
    "Model",
    options=list(AVAILABLE_MODELS.keys()),
    index=list(AVAILABLE_MODELS.keys()).index(DEFAULT_MODEL),
)

if st.session_state["preprocessed_images"]:
    if st.button("🤖 Extract Data From All Images", type="primary"):
        total = len(st.session_state["preprocessed_images"])
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
                        "image_b64": img["b64"],
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
        images = st.session_state["preprocessed_images"]
        batches = [images[i : i + batch_size] for i in range(0, len(images), batch_size)]
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
# Results grid
# --------------------------------------------------------------------------
st.header("4. Results")

if st.session_state["extractions"]:
    cols = st.columns(3)
    for idx, img in enumerate(st.session_state["preprocessed_images"]):
        extraction = st.session_state["extractions"].get(img["image_id"])
        raw_img = _find_image(st.session_state["raw_images"], img["image_id"])
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{img['filename']}**")
                if extraction is None:
                    st.caption("Not yet processed.")
                    continue
                if "error" in extraction:
                    st.error(extraction["error"])
                    continue

                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Original")
                    st.image(f"data:image/png;base64,{raw_img['b64']}", width="stretch")
                with c2:
                    st.caption("Preprocessed (sent to LLM)")
                    st.image(f"data:image/png;base64,{img['b64']}", width="stretch")

                st.json(extraction["parsed"], expanded=False)
else:
    st.info("Run extraction above to see results.")

st.divider()

# --------------------------------------------------------------------------
# Master summary
# --------------------------------------------------------------------------
st.header("5. Deterministic Master Summary")

if st.session_state["merge_result"]:
    result = st.session_state["merge_result"]

    if result["warnings"]:
        for w in result["warnings"]:
            st.error(w)
    else:
        st.success("All fields agreed across images - no discrepancies.")

    st.subheader("Master Record")
    rows = []
    for field in CANONICAL_FIELD_ORDER:
        if field not in result["master_record"]:
            continue
        status = result["field_report"].get(field, {}).get("status", "not_found")
        rows.append(
            {
                "Field": field,
                "Value": result["master_record"][field] or "—",
                "Status": status,
            }
        )
    st.table(rows)
else:
    st.info("Run extraction above to generate the summary.")