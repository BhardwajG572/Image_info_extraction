from collections import defaultdict
from typing import Any, Dict, List
from backend.config import CANONICAL_FIELD_ORDER

_NON_MERGED_KEYS = ("confidence", "raw_text_seen")

def _normalize(value: Any) -> str:
    """Grouping key used ONLY to decide whether two candidate values count
    as "the same" for agreement purposes - never used as the displayed/
    stored value. Strips ALL non-alphanumeric characters (not just
    whitespace), matching field_mapper.py's "tight" normalization, so
    spacing/punctuation-only differences from OCR ("215/60 R 17" vs
    "215/60R17") are correctly recognized as the same value instead of
    triggering a false DISCREPANCY. The value actually stored in
    master_record is always candidates[0]["value"] - the original raw text
    from the first image, verbatim, never rewritten to this normalized
    form."""
    return "".join(ch for ch in str(value).upper() if ch.isalnum())

def merge_extractions(image_extractions: List[Dict]) -> Dict:
    field_values: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    all_fields = set(CANONICAL_FIELD_ORDER)
    warnings: List[str] = []

    for item in image_extractions or []:
        if not isinstance(item, dict): continue
        image_id = item.get("image_id", "unknown")
        parsed = item.get("parsed", {}) or {}

        if not isinstance(parsed, dict): continue
        confidences = parsed.get("confidence", {}) or {}

        for field, value in parsed.items():
            if field in _NON_MERGED_KEYS: continue
            all_fields.add(field)
            if value is None or (isinstance(value, str) and str(value).strip() == ""): continue

            field_values[field].append({
                "image_id": image_id,
                "value": value,
                "confidence": confidences.get(field, None) if isinstance(confidences, dict) else None,
            })

    master: Dict[str, Any] = {}
    field_report: Dict[str, Any] = {}

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
            master[field] = None
            field_report[field] = {"status": "DISCREPANCY", "all_candidates": candidates}
            variant_summary = ", ".join(f"{c['value']!r} (from {c['image_id']})" for c in candidates)
            warnings.append(f"WARNING: Discrepancy found for '{field}': {variant_summary}. No value accepted.")

    # Business Logic for UTQG
    trac_present = bool(master.get("TRAC"))
    temp_present = bool(master.get("TEMP"))

    utqg_value = "UTQG" if trac_present and temp_present else \
                 "UTQG A" if trac_present else \
                 "UTQG B" if temp_present else "UTQG A/B"

    master["UTQG"] = utqg_value
    field_report["UTQG"] = {"status": "agreed", "value": utqg_value, "sources": ["business_logic_derived"]}

    return {
        "master_record": master,
        "field_report": field_report,
        "warnings": warnings,
        "images_processed": [item.get("image_id", "unknown") for item in image_extractions],
    }