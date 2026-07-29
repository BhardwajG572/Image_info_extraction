# backend/field_mapper.py
"""
Maps raw OCR strings (the "extracted_text" list returned by
services.extract_from_image for a single image) into canonical field keys,
using the known-variant table in backend/field_variants.py.

This is a CLASSIFICATION step only: it decides which canonical field a raw
string belongs to. The value stored is always the actual text extracted
from the image, verbatim - never the matched variant/dictionary entry, and
never touched/normalized/rewritten in any way. The downstream
deterministic_merge step is what resolves agreement/discrepancy across
multiple images from those verbatim values.

Matching happens in two stages:

STAGE A - decomposition (tries first): scans a raw line for every place
ANY field's known variant appears as an exact substring (after stripping
spacing/punctuation), greedily claiming the LONGEST matches first so a
more specific/longer pattern wins over a shorter one it contains, then
recurses into non-overlapping remaining stretches of the line. This is
what lets one compound line produce MULTIPLE field values - e.g.
"DOT 1PO KTC305" decomposes into DOT="DOT", DPC="1PO", DMC="KTC305"
instead of the whole line being forced into a single field. The value
stored for each match is the corresponding ORIGINAL substring of the raw
line (exact casing/spacing preserved), never a rewritten/canonical form.

STAGE B - whole-line fallback (only when Stage A finds nothing at all):
the four-tier single-field classifier below, for lines that don't
decompose because they're a typo'd or otherwise-noisy single value with no
exact substring match anywhere (e.g. "AP0LLO"):
  1. loose    - exact match after case/whitespace normalization
  2. tight    - exact match after stripping ALL non-alphanumeric characters
                (handles any spacing/punctuation pattern, not just the
                specific ones listed in field_variants.py, since e.g.
                "215/60 R17", "215/60R17", "21560R17" all reduce to the
                identical tight key regardless of which one was anticipated)
  3. contains - a known variant's core pattern appears fully inside the raw
                text, or vice versa. Needed for compound codes with
                variable suffixes that no finite variant list can fully
                enumerate - e.g. a real DOT code often carries a date/week
                stamp beyond the listed core. Guarded by a minimum match
                length and a longest-match-wins rule so short/generic
                substrings can't hijack unrelated fields.
  4. fuzzy    - similarity-ratio match (stdlib difflib) against all
                variants, only reached when 1-3 all fail. Guarded by a
                similarity floor and a margin-over-runner-up check so it
                only fires when there's one clearly-best field, not a coin
                flip - a wrong fuzzy match is worse than leaving something
                unmatched.

Strings that don't match any known variant (even after fuzzy) are not
dropped - they're kept under "_unmatched" per image so nothing silently
disappears. If more than one raw string in the same image matches the same
field, the first is kept as the field's value and the rest are kept under
"_conflicts" for that field, per image.
"""
import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.field_variants import FIELD_VARIANTS

_PARAMS: Dict[str, List[str]] = FIELD_VARIANTS.get("params", {})

# Fuzzy-tier tuning. Deliberately conservative - misclassifying a value into
# the wrong field is worse than leaving it unmatched, since the wrong field
# then shows a false "agreed" or a confusing DISCREPANCY that isn't real.
FUZZY_MIN_LENGTH = 4        # below this, short/numeric codes require exact match
FUZZY_SCORE_FLOOR = 0.80    # minimum similarity to even be considered
FUZZY_MARGIN = 0.05         # best field must beat the runner-up field by this much

# Contains-tier tuning. A match is only counted if the shorter side (the
# thing actually being matched, not the padding around it) is at least this
# long - stops something like the short "H" (SPEED) variant from matching
# as a substring inside every other longer string.
CONTAINS_MIN_LENGTH = 5

# Decomposition-tier tuning. This tier only does EXACT substring matches
# against the curated variant list (no fuzziness), so short tokens are much
# safer here than in the fuzzy/contains tiers - but still require at least
# this many characters to avoid single/double-character junk matches.
DECOMPOSE_MIN_LENGTH = 3


def _tight(text: str) -> str:
    """Aggressive normalization for matching: uppercase, strip everything
    that isn't a letter or digit. Catches spacing/punctuation OCR noise,
    e.g. "215/60 R17" / "215/60R17" / "21560R17" all reduce to the same
    key."""
    return "".join(ch for ch in str(text).upper() if ch.isalnum())


def _tight_with_mapping(text: str) -> Tuple[str, List[int]]:
    """Like _tight(), but also returns index_map where index_map[i] is the
    index into the ORIGINAL text that tight_string[i] came from. Lets a
    match found in the tight-normalized string be traced back to the exact
    original substring (preserving original spacing/punctuation/casing) for
    use as the stored value."""
    text = str(text)
    tight_chars: List[str] = []
    index_map: List[int] = []
    for i, ch in enumerate(text):
        if ch.isalnum():
            tight_chars.append(ch.upper())
            index_map.append(i)
    return "".join(tight_chars), index_map


def _loose(text: str) -> str:
    """Whitespace-collapsed, uppercased form. Keeps punctuation but
    normalizes spacing/case, matching deterministic_merge's own
    normalization so behavior stays consistent between the two stages."""
    return " ".join(str(text).strip().upper().split())


def _build_lookup() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, List[str]], List[Dict[str, Any]]]:
    """Build loose- and tight-normalized exact-match indexes, plus a
    per-field list of tight-normalized variants for fuzzy matching, from
    FIELD_VARIANTS. Returns (loose_index, tight_index, field_tight_variants,
    conflicts) where conflicts lists any variant string that was claimed by
    more than one field (ambiguous data in FIELD_VARIANTS itself) -
    first field registered wins, matching Python dict iteration order."""
    loose_index: Dict[str, str] = {}
    loose_owner: Dict[str, str] = {}  # for conflict reporting only
    tight_index: Dict[str, str] = {}
    tight_owner: Dict[str, str] = {}
    field_tight_variants: Dict[str, List[str]] = {}
    conflicts: List[Dict[str, Any]] = []

    for field, variants in _PARAMS.items():
        for variant in variants:
            lk = _loose(variant)
            tk = _tight(variant)

            field_tight_variants.setdefault(field, [])
            if tk not in field_tight_variants[field]:
                field_tight_variants[field].append(tk)

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

    return loose_index, tight_index, field_tight_variants, conflicts


def _build_decompose_order(field_tight_variants: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    """Flatten {field: [tight_variants]} into a single (field, variant_tight)
    list sorted longest-variant-first. Decomposition claims matches greedily
    in this order, so a longer/more specific pattern (e.g. a full compound
    code) is tried before a shorter one it might contain, and duplicate
    tight strings across fields are naturally deduplicated by whichever
    field owns that tight string in field_tight_variants (already resolved
    by conflict handling in _build_lookup)."""
    flat: List[Tuple[str, str]] = []
    seen: set = set()
    for field, variants in field_tight_variants.items():
        for variant_tight in variants:
            if len(variant_tight) < DECOMPOSE_MIN_LENGTH:
                continue
            key = (field, variant_tight)
            if key in seen:
                continue
            seen.add(key)
            flat.append(key)
    flat.sort(key=lambda ft: len(ft[1]), reverse=True)
    return flat


_LOOSE_INDEX, _TIGHT_INDEX, _FIELD_TIGHT_VARIANTS, FIELD_VARIANT_CONFLICTS = _build_lookup()
_DECOMPOSE_ORDER = _build_decompose_order(_FIELD_TIGHT_VARIANTS)

if FIELD_VARIANT_CONFLICTS:
    print(
        f"--- FIELD_VARIANTS CONFLICT WARNING --- "
        f"{len(FIELD_VARIANT_CONFLICTS)} variant string(s) are listed under more "
        f"than one field in backend/field_variants.py. This means the losing "
        f"field will never be populated from that exact string. Details:"
    )
    for c in FIELD_VARIANT_CONFLICTS:
        print(f"    {c['variant']!r}: {c['claimed_by']} vs {c['also_claimed_by']} -> {c['resolution']}")


def _contains_classify(tight_raw: str) -> Optional[str]:
    """Substring fallback for compound codes with variable suffixes (date
    stamps, batch numbers) that no finite variant list can enumerate.
    Matches if a known variant is fully contained in the raw text, or the
    raw text is fully contained in a known variant (partial OCR read).
    Longest matched span wins; ties/near-ties across different fields are
    treated as ambiguous and left unmatched rather than guessed."""
    field_best_len: Dict[str, int] = {}

    for field, variants in _FIELD_TIGHT_VARIANTS.items():
        best_len = 0
        for variant_tight in variants:
            if len(variant_tight) < CONTAINS_MIN_LENGTH:
                continue
            if variant_tight in tight_raw:
                best_len = max(best_len, len(variant_tight))
            elif len(tight_raw) >= CONTAINS_MIN_LENGTH and tight_raw in variant_tight:
                best_len = max(best_len, len(tight_raw))
        if best_len > 0:
            field_best_len[field] = best_len

    if not field_best_len:
        return None

    ranked = sorted(field_best_len.items(), key=lambda kv: kv[1], reverse=True)
    best_field, best_len = ranked[0]
    runner_up_len = ranked[1][1] if len(ranked) > 1 else 0

    if runner_up_len == best_len and len(ranked) > 1:
        # Genuine tie between two different fields on the same match
        # length - can't tell them apart, don't guess.
        return None
    return best_field


def _fuzzy_classify(tight_raw: str) -> Optional[str]:
    """Last-resort fallback for spacing/typo variants that weren't caught
    by exact loose/tight matching. Scores tight_raw against every field's
    known variants and only returns a field if there's one clear winner."""
    if len(tight_raw) < FUZZY_MIN_LENGTH:
        return None

    field_scores: Dict[str, float] = {}
    for field, variants in _FIELD_TIGHT_VARIANTS.items():
        best_for_field = 0.0
        for variant_tight in variants:
            ratio = difflib.SequenceMatcher(None, tight_raw, variant_tight).ratio()
            if ratio > best_for_field:
                best_for_field = ratio
        field_scores[field] = best_for_field

    ranked = sorted(field_scores.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked:
        return None

    best_field, best_score = ranked[0]
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if best_score >= FUZZY_SCORE_FLOOR and (best_score - runner_up_score) >= FUZZY_MARGIN:
        return best_field
    return None


# Real-world tire markings print load index and speed rating fused
# together with little or no space ("96H", "96 H") - a single decomposition
# match for the whole token is correct for SPEED but means LOAD_IDX's own
# short 2-digit token (below DECOMPOSE_MIN_LENGTH, and positionally
# overlapping with SPEED's match anyway) never gets extracted on its own.
# This is a narrow, well-defined industry pattern, not a general risk -
# scoped to only fire on values already classified as SPEED.
_LOAD_INDEX_SPEED_RE = re.compile(r"^(\d{2,3})\s*([A-Za-z]{1,2})$")


def _maybe_split_load_index_speed(field: str, value: str) -> List[Tuple[str, str]]:
    """If a SPEED match looks like "<load index digits><speed letters>",
    split it into a LOAD_IDX part and a SPEED part - both taken verbatim
    from the matched substring, not rewritten or guessed at. Leaves
    everything else (including a SPEED match that's just the bare letter,
    e.g. "H") unchanged."""
    if field == "SPEED":
        m = _LOAD_INDEX_SPEED_RE.match(value.strip())
        if m:
            return [("LOAD_IDX", m.group(1)), ("SPEED", m.group(2))]
    return [(field, value)]


def decompose_line(raw_text: str) -> List[Tuple[str, str]]:
    """Scan one raw OCR line for every place a known field variant appears
    as an exact substring, greedily claiming the longest matches first so
    non-overlapping matches can co-exist - this is what lets one compound
    line (e.g. "DOT 1PO KTC305") produce multiple field values instead of
    being forced into a single field.

    Returns a list of (field, original_raw_substring) pairs, in the order
    they appear in the line. Empty list if nothing decomposes (caller
    should fall back to classify_text for the whole-line tiers)."""
    if raw_text is None or not str(raw_text).strip():
        return []

    tight_line, index_map = _tight_with_mapping(raw_text)
    if not tight_line:
        return []

    claimed = [False] * len(tight_line)
    matches: List[Tuple[int, int, str, str]] = []  # (start, end, field, variant_tight)

    for field, variant_tight in _DECOMPOSE_ORDER:
        start = 0
        while True:
            idx = tight_line.find(variant_tight, start)
            if idx == -1:
                break
            end = idx + len(variant_tight)
            if not any(claimed[idx:end]):
                for i in range(idx, end):
                    claimed[i] = True
                matches.append((idx, end, field, variant_tight))
            start = idx + 1  # keep scanning for further non-overlapping occurrences

    if not matches:
        return []

    matches.sort(key=lambda m: m[0])  # restore original left-to-right line order

    results: List[Tuple[str, str]] = []
    for start, end, field, _variant_tight in matches:
        orig_start = index_map[start]
        orig_end = index_map[end - 1] + 1
        raw_substring = str(raw_text)[orig_start:orig_end]
        results.append((field, raw_substring))

    return results


def classify_text(raw_text: str) -> Optional[str]:
    """Return the canonical field key this raw OCR string belongs to, or
    None if it doesn't match any known variant for any field (even after
    fuzzy matching)."""
    if raw_text is None or not str(raw_text).strip():
        return None

    lk = _loose(raw_text)
    if lk in _LOOSE_INDEX:
        return _LOOSE_INDEX[lk]

    tk = _tight(raw_text)
    if tk in _TIGHT_INDEX:
        return _TIGHT_INDEX[tk]

    contains_match = _contains_classify(tk)
    if contains_match is not None:
        return contains_match

    return _fuzzy_classify(tk)


def map_extraction_to_fields(extracted_text: List[str]) -> Dict[str, Any]:
    """Given one image's raw extraction (list of OCR strings), classify each
    string against the known field variants and build a {field: value, ...}
    dict, using the ACTUAL extracted text as the value.

    For each raw line: try decomposition first (may yield multiple field
    values from one compound line, e.g. "DOT 1PO KTC305" -> DOT/DPC/DMC).
    If decomposition finds nothing at all for that line, fall back to
    whole-line classify_text (handles typo'd single-value lines that have
    no exact substring match anywhere, e.g. "AP0LLO").

    Returns a dict with:
      - one key per matched canonical field -> the raw text that matched it
      - "_unmatched": [raw strings/segments that didn't match any known field]
      - "_conflicts": {field: [values that matched a field already claimed
        by an earlier match in this same image]}
    "_unmatched" and "_conflicts" are metadata for visibility, not meant to
    be passed into deterministic_merge - see main.py's /merge endpoint.
    """
    parsed: Dict[str, Any] = {}
    unmatched: List[str] = []
    conflicts: Dict[str, List[str]] = {}

    def _record(field: str, value: str) -> None:
        if field in parsed:
            conflicts.setdefault(field, []).append(value)
        else:
            parsed[field] = value

    for raw in extracted_text or []:
        if raw is None or not str(raw).strip():
            continue

        decomposed = decompose_line(raw)
        if decomposed:
            for field, value in decomposed:
                for split_field, split_value in _maybe_split_load_index_speed(field, value):
                    _record(split_field, split_value)
            continue

        field = classify_text(raw)
        if field is None:
            unmatched.append(raw)
        else:
            for split_field, split_value in _maybe_split_load_index_speed(field, raw):
                _record(split_field, split_value)

    if unmatched:
        parsed["_unmatched"] = unmatched
    if conflicts:
        parsed["_conflicts"] = conflicts

    return parsed