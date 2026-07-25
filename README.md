# Tire Inspection Pipeline

Full-automation tire sidewall inspection: multi-image upload → manual
zoom/pan validation → mirror correction (auto-suggest + manual override) →
multi-model VLM extraction → deterministic (non-LLM) master summary.

Tested end-to-end in this build: FastAPI boots, mirror-detection scores
orientation correctly on real OCR text, JSON parsing survives fenced/messy
LLM output, deterministic merge correctly flags a deliberate size conflict,
and the Streamlit app boots with no import errors.

## 1. Setup (uv + Python 3.12)

```bash
cd tire-inspection-pipeline
uv venv --python 3.12 .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your real Hugging Face token:

```bash
cp .env.example .env
# edit .env -> HF_TOKEN=hf_xxx...
```

### System dependency: Tesseract OCR (for auto mirror-detection)

The auto-suggest flip detector uses `pytesseract`, which needs the
`tesseract-ocr` binary on PATH:

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

If tesseract isn't installed, the app still works — auto-suggestion is
skipped and you fall back to the manual Keep/Flip toggle per image (this
was verified in testing: the code degrades gracefully rather than erroring).

## 2. Run

Two processes, in two terminals:

```bash
# Terminal 1 - backend
uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2 - frontend
uv run streamlit run frontend/app.py
```

Open the Streamlit URL it prints (usually http://localhost:8501).

## 3. Workflow in the UI

1. **Upload** — drop in as many tire images as you have (any angles, any
   session — the uploader accepts multiple files and re-uploads append).
2. **Preview** — click "🔍 Preview" on any thumbnail to open the zoom/pan
   viewer (scroll = zoom, drag = pan, double-click = reset). No third-party
   pip package required — it's a self-contained HTML/JS component.
3. **Run Correction Pipeline** — analyzes every image and shows an
   auto-suggestion (flip / keep) with a confidence score. You can accept
   or manually override each one individually, then "Apply corrections."
4. **Corrected gallery** — same preview capability on the corrected set.
5. **Pick a model** from the dropdown (all 8 models from your registry are
   available) and click **Extract Data From All Images**. Extracted JSON
   appears under each image.
6. **Generate Summary** — pure-Python merge (backend/deterministic_merge.py,
   zero LLM calls). Fields that agree across images are accepted; fields
   that disagree are flagged as `WARNING: Discrepancy Found` with all
   candidate values shown, and a best-guess (highest model confidence) is
   still surfaced so the table isn't empty.

## 4. Project layout

```text
tire-inspection-pipeline/
├── .env.example
├── requirements.txt
├── pyproject.toml
├── backend/
│   ├── main.py                 # FastAPI: /correct-images, /extract, /merge, /models
│   ├── config.py                # HF_TOKEN + AVAILABLE_MODELS registry
│   ├── image_pipeline.py        # OpenCV mirror-detect/flip, lossless PNG round-trip
│   ├── services.py              # HF InferenceClient multimodal chat calls + JSON parsing
│   ├── deterministic_merge.py   # Pure-Python conflict-aware merge
│   └── prompts.py                # Strict JSON-only extraction system prompt
└── frontend/
    ├── app.py                   # Streamlit dashboard, all 6 phases
    └── components.py             # Custom zoom/pan viewer + thumbnail grid
```

## 5. Notes / things to check before production use

- **Model IDs**: a few model ids in your registry look non-standard for
  Hugging Face Hub naming (e.g. `google/gemma-4-31B-it`, `Qwen/Qwen3.6-27B`,
  `zai-org/GLM-4.6V-Flash`). I kept them exactly as you provided since I
  can't verify unreleased/renamed models against my training data — please
  double check each `model_id` resolves on https://huggingface.co/models
  before relying on it, and check whether it actually supports image input
  (some, like Llama-Guard-4, are safety classifiers, not general vision
  extractors — you may want to exclude it from the extraction dropdown or
  repurpose it as a content-safety pre-filter on uploads).
- **`novita` / `fireworks-ai` providers**: these route through HF's
  Inference Providers marketplace, not HF's own infra — pricing/availability
  differs per provider and depends on your HF account having provider access
  enabled.
- **Discrepancy resolution**: currently automatic (highest-confidence value
  wins as "best guess," original is still shown). If you want a hard stop
  requiring human sign-off before the summary is finalized, that's a small
  change to Phase 6 in `frontend/app.py` (gate on `warnings` being empty).
- The zoom/pan viewer supports single-finger pan on touch devices but not
  pinch-to-zoom yet — flag if you need that added.
