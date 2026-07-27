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

_NON_MERGED_KEYS = ("confidence", "raw_text_seen")


def _normalize(value: Any) -> str:
    """Normalizes strings to ignore case and minor whitespace differences during comparison."""
    return " ".join(str(value).strip().upper().split())


def merge_extractions(image_extractions: list[dict]) -> dict:
    """
    image_extractions: list of
      {
        "image_id": str,
        "parsed": { field: value, ..., "confidence": {field: score} }
      }
    """
    field_values: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_fields = set(CANONICAL_FIELD_ORDER)
    warnings: list[str] = []

    for item in image_extractions or []:
        if not isinstance(item, dict):
            warnings.append(f"Skipping invalid extraction entry: {item!r}")
            continue

        image_id = item.get("image_id", "unknown")
        parsed = item.get("parsed", {}) or {}
        if not isinstance(parsed, dict):
            warnings.append(
                f"Skipping invalid parsed payload for image '{image_id}'"
            )
            continue

        confidences = parsed.get("confidence", {}) or {}
        if not isinstance(confidences, dict):
            confidences = {}

        for field, value in parsed.items():
            if field in _NON_MERGED_KEYS:
                continue
            all_fields.add(field)
            # Skip empty or null values
            if value is None or (isinstance(value, str) and str(value).strip() == ""):
                continue

            field_values[field].append(
                {
                    "image_id": image_id,
                    "value": value,
                    "confidence": confidences.get(field, None),
                }
            )

    master: dict[str, Any] = {}
    field_report: dict[str, Any] = {}

    # Sort fields so canonical fields show up first, followed by any extras found
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
            # PERFECT MATCH: All extractions agree
            accepted_value = candidates[0]["value"]
            master[field] = accepted_value
            field_report[field] = {
                "status": "agreed",
                "value": accepted_value,
                "sources": [c["image_id"] for c in candidates],
            }
        else:
            # STRICT NO-GUESSING LOGIC
            master[field] = None
            field_report[field] = {
                "status": "DISCREPANCY",
                "all_candidates": candidates,
            }
            variant_summary = ", ".join(
                f"{c['value']!r} (from {c['image_id']})" for c in candidates
            )
            warnings.append(
                f"WARNING: Discrepancy found for '{field}': {variant_summary}. "
                "No value was accepted because the extractions disagree."
            )

    # ==========================================
    # CUSTOM BUSINESS LOGIC FOR UTQG
    # ==========================================
    # Check if TRAC and TEMP successfully made it into the master record
    trac_present = bool(master.get("TRAC"))
    temp_present = bool(master.get("TEMP"))

    if trac_present and temp_present:
        utqg_value = "UTQG"
    elif trac_present and not temp_present:
        utqg_value = "UTQG A"
    elif not trac_present and temp_present:
        utqg_value = "UTQG B"
    else:
        utqg_value = "UTQG A/B"

    # Force the derived UTQG value into the master record
    master["UTQG"] = utqg_value
    field_report["UTQG"] = {
        "status": "agreed",
        "value": utqg_value,
        "sources": ["business_logic_derived"]
    }
    # ==========================================

    return {
        "master_record": master,
        "field_report": field_report,
        "warnings": warnings,
        "images_processed": [
            item.get("image_id", "unknown") for item in image_extractions
        ],
    }