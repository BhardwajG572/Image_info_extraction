# backend/deterministic_merge.py
from collections import defaultdict
from typing import Any, Dict, List, Optional
from backend.config import CANONICAL_FIELD_ORDER, SKU_SPECIFICATIONS, SIDE_SPECIFIC_RULES
from backend.field_variants import FIELD_VARIANTS

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

def merge_extractions(image_extractions: List[Dict], sku_specifications: Optional[Dict] = None) -> Dict:
    active_sku_specs = sku_specifications if sku_specifications is not None else SKU_SPECIFICATIONS
    top_values: Dict[str, List[str]] = defaultdict(list)
    bottom_values: Dict[str, List[str]] = defaultdict(list)
    all_fields = set(CANONICAL_FIELD_ORDER) | set(active_sku_specs.keys())

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
        spec_val = active_sku_specs.get(field)
        
        if field == "Utqg Marking":
            top_trac = top_values.get("Traction")
            top_temp = top_values.get("Temperature")
            if top_trac and top_temp:
                top_values[field] = ["UTQG"]
            elif top_trac:
                top_values[field] = ["UTQG A"]
            elif top_temp:
                top_values[field] = ["UTQG B"]
            else:
                top_values[field] = ["UTQG A/B"]

            bot_trac = bottom_values.get("Traction")
            bot_temp = bottom_values.get("Temperature")
            if bot_trac and bot_temp:
                bottom_values[field] = ["UTQG"]
            elif bot_trac:
                bottom_values[field] = ["UTQG A"]
            elif bot_temp:
                bottom_values[field] = ["UTQG B"]
            else:
                bottom_values[field] = ["UTQG A/B"]
                
        top_agreed = _get_agreed_value(top_values.get(field, []))
        bot_agreed = _get_agreed_value(bottom_values.get(field, []))
        
        if not spec_val and not top_agreed and not bot_agreed:
            continue  # Skip empty fields entirely
            
        top_tight = _normalize(top_agreed)
        bot_tight = _normalize(bot_agreed)
        
        # Determine all acceptable normalized variants for this field
        valid_variants = [_normalize(v) for v in FIELD_VARIANTS.get("params", {}).get(field, [])]
        
        # spec_val from the frontend can be a comma-separated list of acceptable variants
        if spec_val:
            for variant in str(spec_val).split(','):
                variant_tight = _normalize(variant)
                if variant_tight:
                    valid_variants.append(variant_tight)
        
        # Determine rules for this parameter
        required_side = SIDE_SPECIFIC_RULES.get(field, "Top & Bottom")
        
        # --- Evaluate TOP Status ---
        status_top = "NF"
        if top_values.get(field) and top_agreed and required_side in ["Top", "Top & Bottom"]:
            if not spec_val or (spec_val and top_tight in valid_variants):
                status_top = "OK"
                
        # --- Evaluate BOTTOM Status ---
        status_bottom = "NF"
        if bottom_values.get(field) and bot_agreed and required_side in ["Bottom", "Top & Bottom"]:
            if not spec_val or (spec_val and bot_tight in valid_variants):
                status_bottom = "OK"

        # Handle explicit empty specs
        if spec_val == "" and field != "Utqg Marking":
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