import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SKU_SPECIFICATIONS, CANONICAL_FIELD_ORDER, SIDE_SPECIFIC_RULES
from field_variants import FIELD_VARIANTS

def generate_default_skus():
    sku_data = {
        "APOLLO APTERRA CROSS 215/60 R17": {
            "metadata": {
                "material_code": "RLGIW0APC3AH2",
                "description": "215/60 R17 96H APTERRA CROSS (MS) TL - D",
                "rev": "1",
                "date": "-",
                "gt_code": "GT8048",
                "gt_iden": "WHITE",
                "gt_wgt": "10.015 ± 0.3 kg",
                "plant": "1007 - Apollo Chennai"
            },
            "parameters": [
                {"name": "Size designation", "uom": "", "location": "Top & Bottom", "specification": "215/60 R17", "variants": ["215/60 R17", "215/60R17", "215/60 r 17", "215/60r17", "215 60 R 17", "215/60 R 17", "215/60R 17", "21560R17"]},
                {"name": "Load index", "uom": "", "location": "Top & Bottom", "specification": "96", "variants": ["96"]},
                {"name": "Speed index", "uom": "", "location": "Top & Bottom", "specification": "H", "variants": ["H", "96H", "96 h", "96 H"]},
                {"name": "Brand", "uom": "", "location": "Top & Bottom", "specification": "APOLLO", "variants": ["APOLLO", "apollo", "aPOLLO", "ap0llo", "ap0ll0"]},
                {"name": "Productline", "uom": "", "location": "Top & Bottom", "specification": "APTERRA CROSS", "variants": ["APTERRA CROSS", "TERRA CROSS", "apterra cross", "CROSS", "APTERRA", "Apterra Cross", "APTERRA-CROSS", "APTERRACROSS"]},
                {"name": "Tubetype/tubeless", "uom": "", "location": "Top & Bottom", "specification": "RADIAL TUBELESS", "variants": ["RADIAL TUBELESS", "TUBELESS"]},
                {"name": "Load index class", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "DOT marking", "uom": "", "location": "Top & Bottom", "specification": "DOT", "variants": ["DOT", "D0T"]},
                {"name": "DOT Plant Code", "uom": "", "location": "Top & Bottom", "specification": "1P0", "variants": ["1P0", "1PO", "iPO", "IPO", "IP0"]},
                {"name": "DOT Manufacturers Code", "uom": "", "location": "Top & Bottom", "specification": "KTC305", "variants": ["KTC305", "KTC3O5", "KTC30S"]},
                {"name": "Utqg Marking", "uom": "", "location": "Top & Bottom", "specification": "YES", "variants": ["YES", "UTQG", "UTQG A", "UTQG B", "UTQG A/B"]},
                {"name": "Temperature", "uom": "", "location": "Top & Bottom", "specification": "A", "variants": ["A", "TEMPERATURE A", "Temperature A", "TEMPERATUREA"]},
                {"name": "Traction", "uom": "", "location": "Top & Bottom", "specification": "A", "variants": ["A", "TRACTION A", "Traction A", "TRACTIONA"]},
                {"name": "Tread wear", "uom": "", "location": "Top & Bottom", "specification": "460", "variants": ["460", "TREADWEAR 460", "Treadwear 460", "TREADWEAR460"]},
                {"name": "Tread Wear Indicator (TWI)", "uom": "mm", "location": "Top & Bottom", "specification": "YES", "variants": ["YES"]},
                {"name": "ISI Marking", "uom": "", "location": "Bottom", "specification": "IS:15633 CM/L-3382863", "variants": ["IS:15633 CM/L-3382863", "IS:15633CM/L3382863", "IS:15633", "IS15633", "IS 15633", "CM/L3382863", "GM/L-3382863", "GM/L 3382863", "3382863"]},
                {"name": "E-appr. code (S/W/R)", "uom": "", "location": "Top & Bottom", "specification": "E4 0211093 S2WR2", "variants": ["E4 0211093 S2WR2", "E40211093 S2WR2", "E4 0211093S2WR2", "E40211093S2WR2", "0211093 S2WR2", "0211093S2WR2"]},
                {"name": "E-approval code", "uom": "", "location": "Top & Bottom", "specification": "E4 02119426", "variants": ["E4 02119426", "E402119426", "02119426"]},
                {"name": "Inmetro 200 engraved", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Indonesia certificate (SNI)", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Philipinnes certificate (PBS)", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "AIS Marking", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "China certificate (CCC)", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Winter indication", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "M+S Marking", "uom": "", "location": "Top & Bottom", "specification": "M+S", "variants": ["M+S", "MS", "M S", "M&S"]},
                {"name": "Directional", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Inner side", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Outer side", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "EV Ready", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Sustainability", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Giugiaro Design", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Adventure comfort", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "OE SPECIFIC MARKING", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Made in", "uom": "", "location": "Top & Bottom", "specification": "MADE IN INDIA", "variants": ["MADE IN INDIA", "MADE IN IND1A", "MADE IN INDlA", "MADE IN INDIA ", "MADEININDIA", "INDIA", "iNDIA"]},
                {"name": "Safety warning", "uom": "", "location": "Top", "specification": "MANDATORY", "variants": ["MANDATORY", "WARNING", "Warning", "SAFETY WARNING", "SAFETY WARNIN", "SAFETY WARNI", "SAFETY WARN", "SAFETY WA", "SAFETY W", "SAFETY ", "SAFETY"]},
                {"name": "Plies tread", "uom": "", "location": "Top & Bottom", "specification": "1PE+2STL+1NYL", "variants": ["1PE+2STL+1NYL", "TREAD: 1 POLYESTER + 2 STEEL + 1 NYLON", "TREAD 1 POLYESTER + 2 STEEL", "1 POLYESTER + 2 STEEL + 1 NYLON", "POLYESTER + 2 STEEL + 1 NYLON", "TREAD: 2 PLIES"]},
                {"name": "Plies sidewall", "uom": "", "location": "Top & Bottom", "specification": "2 POLYESTER", "variants": ["2 POLYESTER", "SIDE WALL:2 POLYESTER", "SIDE WALL:2", "SIDE WALL 2", "SIDE WALL 2 POLYESTER", "2POLYESTER"]},
                {"name": "Maximum Inflation Pressure (KPA)", "uom": "kPa", "location": "Top & Bottom", "specification": "350", "variants": ["350", "350KPA", "350 KPA", "350kPa", "350 KPA", "350kpa"]},
                {"name": "Maximum Inflation Pressure (PSI)", "uom": "psi", "location": "Top & Bottom", "specification": "51", "variants": ["51", "51 PSI", "51PSI", "51 psi", "51psi"]},
                {"name": "Maximum Load (KG)", "uom": "kg", "location": "Top & Bottom", "specification": "710", "variants": ["710", "710 KG", "710KG", "710 kg", "710kg"]},
                {"name": "Maximum Load (LBS)", "uom": "lbs", "location": "Top & Bottom", "specification": "1565", "variants": ["1565", "1565 LBS", "1565LBS", "1565 lbs", "1565lbs"]},
                {"name": "Maximum Load Single (LBS)", "uom": "lbs", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Load Single (KG)", "uom": "kg", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Load Dual (LBS)", "uom": "lbs", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Load Dual (KG)", "uom": "kg", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Inflation Pressure Single (PSI)", "uom": "psi", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Inflation Pressure Single (KPA)", "uom": "kPa", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Inflation Pressure Dual (PSI)", "uom": "psi", "location": "", "specification": "-", "variants": []},
                {"name": "Maximum Inflation Pressure Dual (KPA)", "uom": "kPa", "location": "", "specification": "-", "variants": []},
                {"name": "Load range", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Ply rating", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "p_max testing", "uom": "kPa", "location": "", "specification": "-", "variants": []},
                {"name": "Mould Drawing No", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Tyre Mould Segment", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Tyre Side Plate Id", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "FITMENT", "uom": "", "location": "", "specification": "-", "variants": []},
                {"name": "Manufacture date code", "uom": "", "location": "Top & Bottom", "specification": "WWYY", "variants": ["WWYY"]},
                {"name": "Mold reference number", "uom": "", "location": "Top & Bottom", "specification": "B8524-**", "variants": ["B8524-**", "B8524", "B8S24-32", "B8524-32", "B8S24", "b8524", "B 8524", "B 8524", "B8524", "8524"]},
                {"name": "Cure Tyre Identification", "uom": "", "location": "", "specification": "WHITE", "variants": ["WHITE"]}
            ]
        }
    }
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dynamic_skus.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sku_data, f, indent=4)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    generate_default_skus()
