# backend/prompts.py

OCR_JSON_PROMPT = """You are an industrial OCR system reading text embossed on a tyre sidewall.

TASK: Extract ALL text visible on the tyre sidewall and output it in JSON format.

RULES:
- Return a valid JSON object with a single key "extracted_text" containing a list of strings.
- Each piece of information should be a separate string in the list.
- Preserve exact spelling, numbers, and punctuation
- Do NOT add explanations, headers, or summaries
- If you see partial text, still include it
- If you cannot read something, do NOT guess or fill in, just omit it
- Common tyre markings to look for: size (e.g. 295/90R20), brand, model name, load index, speed rating, PSI/kPa values, DOT code, MADE IN INDIA, isi marking, sni markings, steel ply info
- MIRRORED AND INVERTED TEXT AWARENESS: The image provided to you has been run through a preprocessing pipeline and has been horizontally flipped (mirrored) or rotated. You MUST actively read mirrored, backward, or upside-down text. Mentally reverse the characters to extract the correct, standard values. DO NOT omit text just because it appears backwards.

Example Output:
{
  "extracted_text": [
    "APOLLO",
    "295/90R20",
    "DOT 1P0 KTC305"
  ]
}"""

USER_OCR_INSTRUCTION = (
    "Examine this tire sidewall image and extract all visible text line by line. "
    "NOTE: The image has been horizontally flipped (mirrored). Read the backwards text carefully and reverse it to standard English/Numbers. "
    "Return the result strictly as JSON."
)