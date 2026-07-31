# backend/deterministic_merge.py
from collections import defaultdict
from typing import Any, Dict, List, Optional
from backend.config import CANONICAL_FIELD_ORDER, SKU_SPECIFICATIONS, SIDE_SPECIFIC_RULES

_NON_MERGED_KEYS = ("confidence", "raw_text_seen")

def _normalize(value: Any) -> str:
    """Strips ALL non-alphanumeric characters for robust compliance matching."""
    if value is None: return ""
    return "".join(ch for ch in str(value).upper() if ch.isalnum())

def _get_agreed_value(candidates: List[str]) -> Optional[str]:
    """Returns the verbatim value if all candidates tightly match each other."""
    if not candidates: return None
    distinct = {}
    for c in candidates:
        key = _normalize(c)
        distinct.setdefault(key, []).append(c)
    if len(distinct) == 1:
        return candidates[0]  # Return the first verbatim string
    return None  # Discrepancy between images on the same side

def merge_extractions(image_extractions: List[Dict]) -> Dict:
    top_values: Dict[str, List[str]] = defaultdict(list)
    bottom_values: Dict[str, List[str]] = defaultdict(list)
    all_fields = set(CANONICAL_FIELD_ORDER) | set(SKU_SPECIFICATIONS.keys())

    for item in image_extractions or []:
        if not isinstance(item, dict): continue
        side = item.get("side", "Unknown")
        parsed = item.get("parsed", {}) or {}
        
        if not isinstance(parsed, dict): continue

        for field, value in parsed.items():
            if field in _NON_MERGED_KEYS: continue
            all_fields.add(field)
            if value is None or (isinstance(value, str) and str(value).strip() == ""): continue
            
            if side == "Top":
                top_values[field].append(value)
            elif side == "Bottom":
                bottom_values[field].append(value)

    compliance_report = []

    ordered_fields = [f for f in CANONICAL_FIELD_ORDER if f in all_fields]
    ordered_fields += sorted(f for f in all_fields if f not in CANONICAL_FIELD_ORDER)

    for field in ordered_fields:
        spec_val = SKU_SPECIFICATIONS.get(field)
        top_agreed = _get_agreed_value(top_values.get(field, []))
        bot_agreed = _get_agreed_value(bottom_values.get(field, []))
        
        if not spec_val and not top_agreed and not bot_agreed:
            continue  # Skip empty fields entirely
            
        spec_tight = _normalize(spec_val)
        top_tight = _normalize(top_agreed)
        bot_tight = _normalize(bot_agreed)
        
        # Determine rules for this parameter
        required_side = SIDE_SPECIFIC_RULES.get(field, "Top & Bottom")
        
        # --- Evaluate TOP Status ---
        status_top = "NF"
        if top_agreed:
            if required_side in ["Top", "Top & Bottom"]:
                if spec_val and top_tight == spec_tight:
                    status_top = "OK"
                elif not spec_val: # If no spec was defined but we found it, mark OK
                    status_top = "OK"
            else:
                status_top = "NF" # Found on wrong side
                
        # --- Evaluate BOTTOM Status ---
        status_bottom = "NF"
        if bot_agreed:
            if required_side in ["Bottom", "Top & Bottom"]:
                if spec_val and bot_tight == spec_tight:
                    status_bottom = "OK"
                elif not spec_val:
                    status_bottom = "OK"
            else:
                status_bottom = "NF" # Found on wrong side

        # Handle explicit empty specs (e.g., UTQG should be empty)
        if spec_val == "":
            if top_agreed: status_top = "NF"
            if bot_agreed: status_bottom = "NF"

        # Update table structure to output OK/NF directly in the Mould columns
        compliance_report.append({
            "Parameters": field,
            "Location Requirement": required_side,
            "Specification": spec_val if spec_val else "—",
            "Mould_Top": status_top,
            "Mould_Bottom": status_bottom
        })

    return {
        "compliance_report": compliance_report,
        "images_processed": [item.get("image_id", "unknown") for item in image_extractions],
    }