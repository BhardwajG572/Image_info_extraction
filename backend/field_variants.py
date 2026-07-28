# backend/field_variants.py
"""
Known OCR-noise variants for each canonical tire field. Used by
backend/field_mapper.py to classify a raw extracted text string (from
services.extract_from_image's "extracted_text" list) into the canonical
field it belongs to.

NOTE: this is a classification aid only. The value stored against a field
is always the actual raw text extracted from the image, never one of these
variant strings - see field_mapper.map_extraction_to_fields.
"""

FIELD_VARIANTS = {
    "params": {
        "SIZE":     ["215/60 R17","215/60R17","215/60 r 17","215/60r17","215 60 R 17","215/60 R 17","215/60R 17","215/60 R17","21560R17"],
        "BRAND":    ["APOLLO","apollo","aPOLLO","ap0llo","ap0ll0"],
        "MODEL":    ["APTERRA CROSS","TERRA CROSS","apterra cross","CROSS","APTERRA","Apterra Cross","APTERRA-CROSS","APTERRACROSS"],
        "MOULD":    ["B8524","B8S24-32","B8524-32","B8S24","b8524","B 8524","B 8524","B8524","8524"],
        "LOAD_IDX": ["96","96"],
        "KPA":      ["350","350KPA","350 KPA","350kPa","350 KPA","350kpa"],
        "PSI":      ["51"],
        "LOAD_KG":   ["710"],
        "LOAD_LBS":   ["1565","1565 LBS","1565LBS", "1565 lbs","1565lbs"],
        "SPEED":    ["H","96H","96 h","96 H","215/60 R 17 96 H"],
        "SAFETY":   ["WARNING","Warning","SAFETY WARNING","SAFETY WARNIN","SAFETY WARNI","SAFETY WARN","SAFETY WA","SAFETY W","SAFETY ","SAFETY"],
        "TYPE":     ["TUBELESS"],
        "MARK": ["M+S", "MS", "M S", "M&S", "M S", "M+S"],
        "TRAC": ["TRACTION A","Traction A","TRACTIONA"],
        "TEMP": ["TEMPERATURE A","Temperature A","TEMPERATUREA"],
        "TWEAR": ["TREADWEAR 460","Treadwear 460","TREADWEAR460","460"],
        "UTQG": ["UTQG","UTQG A","UTQG B","UTQG A/B"],
        "INDIA":    ["MADE IN INDIA","MADE IN IND1A","MADE IN INDlA","MADE IN INDIA ","MADEININDIA","INDIA","iNDIA"],
        "DOT":      ["DOT","D0T","1P0 KTC305"],
        "DPC": ["1P0","1PO","iPO","IPO","IP0"],
        "DMC": ["KTC305","KTC3O5","KTC30S"],
        "P_TREAD":  ["TREAD: 1 POLYESTER + 2 STEEL + 1 NYLON","TREAD 1 POLYESTER + 2 STEEL","1 POLYESTER + 2 STEEL + 1 NYLON","POLYESTER + 2 STEEL + 1 NYLON","TREAD: 2 PLIES"],
        "SIDEWALL": ["SIDE WALL:2 POLYESTER","SIDE WALL:2","SIDE WALL 2","SIDE WALL 2 POLYESTER","2 POLYESTER","2POLYESTER"],
        "NOISE": ["E4 0211093 S2WR2","E40211093 S2WR2","E4 0211093S2WR2","E40211093S2WR2","0211093 S2WR2","0211093S2WR2"],
        "ECE": ["E4 02119426","E402119426","02119426"],
        "ISI": ["IS:15633CM/L3382863","IS:15633","IS15633","IS 15633","IS:15633CM/L3382863","IS:15633CM/L3382863","CM/L3382863","GM/L-3382863","GM/L 3382863","3382863"],
        #"SNI": ["SNI","sni"],

    },
    #"side_specific": {"SAFETY": "TOP", "SNI":"BOT"}
    "side_specific": {"SAFETY": "TOP","ISI": "BOT"}
}