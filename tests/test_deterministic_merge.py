from backend.deterministic_merge import merge_extractions


def test_merge_extractions_ignores_invalid_parsed_payloads():
    result = merge_extractions(
        [
            {"image_id": "img-1", "parsed": "not a dictionary"},
            {"image_id": "img-2", "parsed": {"BRAND": "Michelin", "confidence": {"BRAND": 0.95}}},
        ]
    )

    assert result["master_record"]["BRAND"] == "Michelin"
    assert result["field_report"]["BRAND"]["status"] == "agreed"
