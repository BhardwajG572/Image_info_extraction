"""
Phase 6: Deterministic Master Synthesis.

Deliberately contains ZERO LLM calls. Combining N per-image JSON extractions
into one master record is a pure data-merging problem, and doing it with an
LLM would reintroduce the exact hallucination risk this pipeline was built
to eliminate. This module is fully unit-testable and reproducible.
"""
from collections import defaultdict
from typing import Any, Optional

from backend.config import CANONICAL_FIELD_ORDER

# Add 'extracted_lines' to bypass standard string comparison logic
_NON_MERGED_KEYS = ("confidence", "raw_text_seen", "extracted_lines")


def _normalize(value: Any) -> str:
    """Safely normalizes strings or lists for comparison."""
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    return " ".join(str(value).strip().upper().split())


def merge_extractions(image_extractions: list[dict]) -> dict:
    """
    image_extractions: list of
      {
        "image_id": str,
        "parsed": { field: value, ..., "confidence": {field: score}, "extracted_lines": [...] }
      }
    """
    field_values: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_fields = set(CANONICAL_FIELD_ORDER)
    
    master: dict[str, Any] = {}
    warnings: list[str] = []
    field_report: dict[str, Any] = {}

    # --- Special Handling for pure OCR Line Extraction ---
    master_lines = []
    seen_lines = set()

    for item in image_extractions:
        image_id = item.get("image_id", "unknown")
        parsed = item.get("parsed", {}) or {}
        confidences = parsed.get("confidence", {}) or {}

        # Safely extract and deduplicate OCR lines across all images
        lines = parsed.get("extracted_lines", [])
        if isinstance(lines, list):
            for line in lines:
                norm_line = _normalize(line)
                if norm_line and norm_line not in seen_lines:
                    seen_lines.add(norm_line)
                    master_lines.append(line)

        # Standard field extraction
        for field, value in parsed.items():
            if field in _NON_MERGED_KEYS:
                continue
            all_fields.add(field)
            if value is None or str(value).strip() == "":
                continue
            
            field_values[field].append(
                {
                    "image_id": image_id,
                    "value": value,
                    "confidence": confidences.get(field, None),
                }
            )

    # Attach aggregated OCR lines to the master record
    if master_lines:
        master["extracted_lines"] = master_lines
        field_report["extracted_lines"] = {
            "status": "aggregated",
            "sources": [item.get("image_id", "unknown") for item in image_extractions]
        }

    # --- Standard Handling for Structured JSON Schema ---
    ordered_fields = [f for f in CANONICAL_FIELD_ORDER if f in all_fields and f not in _NON_MERGED_KEYS]
    ordered_fields += sorted(f for f in all_fields if f not in CANONICAL_FIELD_ORDER and f not in _NON_MERGED_KEYS)

    for field in ordered_fields:
        candidates = field_values.get(field, [])
        if not candidates:
            master[field] = None
            field_report[field] = {"status": "not_found", "sources": []}
            continue

        distinct = {}
        for c in candidates:
            key = _normalize(c["value"])
            distinct.setdefault(key, []).append(c)

        if len(distinct) == 1:
            accepted_value = candidates[0]["value"]
            master[field] = accepted_value
            field_report[field] = {
                "status": "agreed",
                "value": accepted_value,
                "sources": [c["image_id"] for c in candidates],
            }
        else:
            def sort_key(c):
                conf = c["confidence"]
                return conf if isinstance(conf, (int, float)) else -1

            best = max(candidates, key=sort_key)
            master[field] = best["value"]
            field_report[field] = {
                "status": "DISCREPANCY",
                "best_guess": best["value"],
                "best_guess_source": best["image_id"],
                "all_candidates": candidates,
            }
            variant_summary = ", ".join(
                f"{c['value']!r} (from {c['image_id']})" for c in candidates
            )
            warnings.append(
                f"WARNING: Discrepancy found for '{field}': {variant_summary}. "
                f"Best guess used: {best['value']!r} (from {best['image_id']})."
            )

    return {
        "master_record": master,
        "field_report": field_report,
        "warnings": warnings,
        "images_processed": [
            item.get("image_id", "unknown") for item in image_extractions
        ],
    }