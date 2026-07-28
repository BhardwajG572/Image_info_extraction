# backend/field_mapper.py
"""
Maps raw OCR strings (the "extracted_text" list returned by
services.extract_from_image for a single image) into canonical field keys,
using the known-variant table in backend/field_variants.py.

This is a CLASSIFICATION step only: it decides which canonical field a raw
string belongs to. The value stored is always the actual text extracted
from the image, never the matched variant/dictionary entry - the
downstream deterministic_merge step is what resolves agreement/discrepancy
across multiple images.

Strings that don't match any known variant are not dropped - they're kept
under "_unmatched" per image so nothing silently disappears. If more than
one raw string in the same image matches the same field, the first is kept
as the field's value and the rest are kept under "_conflicts" for that
field, per image.
"""
from typing import Any, Dict, List, Tuple

from backend.field_variants import FIELD_VARIANTS

_PARAMS: Dict[str, List[str]] = FIELD_VARIANTS.get("params", {})


def _tight(text: str) -> str:
    """Aggressive normalization for matching: uppercase, strip everything
    that isn't a letter or digit. Catches spacing/punctuation OCR noise,
    e.g. "215/60 R17" / "215/60R17" / "21560R17" all reduce to the same
    key."""
    return "".join(ch for ch in str(text).upper() if ch.isalnum())


def _loose(text: str) -> str:
    """Whitespace-collapsed, uppercased form. Keeps punctuation but
    normalizes spacing/case, matching deterministic_merge's own
    normalization so behavior stays consistent between the two stages."""
    return " ".join(str(text).strip().upper().split())


def _build_lookup() -> Tuple[Dict[str, str], Dict[str, str], List[Dict[str, Any]]]:
    """Build loose- and tight-normalized lookup indexes from FIELD_VARIANTS.
    Returns (loose_index, tight_index, conflicts) where conflicts lists any
    variant string that was claimed by more than one field (ambiguous data
    in FIELD_VARIANTS itself) - first field registered wins, matching Python
    dict iteration order."""
    loose_index: Dict[str, str] = {}
    loose_owner: Dict[str, str] = {}  # for conflict reporting only
    tight_index: Dict[str, str] = {}
    tight_owner: Dict[str, str] = {}
    conflicts: List[Dict[str, Any]] = []

    for field, variants in _PARAMS.items():
        for variant in variants:
            lk = _loose(variant)
            tk = _tight(variant)

            if lk in loose_owner and loose_owner[lk] != field:
                conflicts.append(
                    {
                        "variant": variant,
                        "normalized": lk,
                        "claimed_by": loose_owner[lk],
                        "also_claimed_by": field,
                        "resolution": f"assigned to '{loose_owner[lk]}' (first-registered wins)",
                    }
                )
            else:
                loose_owner[lk] = field
                loose_index[lk] = field

            if tk in tight_owner and tight_owner[tk] != field:
                # Only record if not already flagged via the loose check above
                if not (lk in loose_owner and loose_owner[lk] != field):
                    conflicts.append(
                        {
                            "variant": variant,
                            "normalized": tk,
                            "claimed_by": tight_owner[tk],
                            "also_claimed_by": field,
                            "resolution": f"assigned to '{tight_owner[tk]}' (first-registered wins)",
                        }
                    )
            else:
                tight_owner[tk] = field
                tight_index[tk] = field

    return loose_index, tight_index, conflicts


_LOOSE_INDEX, _TIGHT_INDEX, FIELD_VARIANT_CONFLICTS = _build_lookup()

if FIELD_VARIANT_CONFLICTS:
    print(
        f"--- FIELD_VARIANTS CONFLICT WARNING --- "
        f"{len(FIELD_VARIANT_CONFLICTS)} variant string(s) are listed under more "
        f"than one field in backend/field_variants.py. This means the losing "
        f"field will never be populated from that exact string. Details:"
    )
    for c in FIELD_VARIANT_CONFLICTS:
        print(f"    {c['variant']!r}: {c['claimed_by']} vs {c['also_claimed_by']} -> {c['resolution']}")


def classify_text(raw_text: str) -> str | None:
    """Return the canonical field key this raw OCR string belongs to, or
    None if it doesn't match any known variant for any field."""
    if raw_text is None or not str(raw_text).strip():
        return None

    lk = _loose(raw_text)
    if lk in _LOOSE_INDEX:
        return _LOOSE_INDEX[lk]

    tk = _tight(raw_text)
    if tk in _TIGHT_INDEX:
        return _TIGHT_INDEX[tk]

    return None


def map_extraction_to_fields(extracted_text: List[str]) -> Dict[str, Any]:
    """Given one image's raw extraction (list of OCR strings), classify each
    string against the known field variants and build a {field: value, ...}
    dict, using the ACTUAL extracted text as the value.

    Returns a dict with:
      - one key per matched canonical field -> the raw text that matched it
      - "_unmatched": [raw strings that didn't match any known field]
      - "_conflicts": {field: [raw strings that matched a field already
        claimed by an earlier string in this same image]}
    "_unmatched" and "_conflicts" are metadata for visibility, not meant to
    be passed into deterministic_merge - see main.py's /merge endpoint.
    """
    parsed: Dict[str, Any] = {}
    unmatched: List[str] = []
    conflicts: Dict[str, List[str]] = {}

    for raw in extracted_text or []:
        field = classify_text(raw)
        if field is None:
            unmatched.append(raw)
            continue
        if field in parsed:
            conflicts.setdefault(field, []).append(raw)
        else:
            parsed[field] = raw

    if unmatched:
        parsed["_unmatched"] = unmatched
    if conflicts:
        parsed["_conflicts"] = conflicts

    return parsed