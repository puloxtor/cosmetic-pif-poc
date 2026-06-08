"""
Тестове за евристичния парсър (Слой 2). Работим върху представителни редове
(както биха излезли от координатното извличане), без реални PDF-и.
"""
from pif_engine.extraction.parse import (
    parse_composition, parse_fragrance, looks_like_fragrance,
)
from pif_engine.extraction.draft import raw_material_draft, to_yaml
from pif_engine.extraction.filter import filter_candidates


# ---------- композиция: диапазони и точни % (Phenbiox / Vitapherole) ----------

def test_composition_range_takes_low_high():
    lines = ["HELIANTHUS ANNUUS SEED OIL 45-55 8001-21-6 232-273-9"]
    out = parse_composition(lines)
    assert out == [{"inci_name": "HELIANTHUS ANNUUS SEED OIL", "range": [45.0, 55.0]}]


def test_composition_exact_pct_with_comma():
    lines = ["TOCOPHEROL 0,9 59-02-9"]
    out = parse_composition(lines)
    assert out == [{"inci_name": "TOCOPHEROL", "pct": 0.9}]


def test_composition_single_inci_100():
    lines = ["Ricinus Communis Seed Oil 100 8001-79-4"]
    out = parse_composition(lines)
    assert out == [{"inci_name": "Ricinus Communis Seed Oil", "pct": 100.0}]


def test_composition_skips_pure_text():
    lines = ["Composition / Composizione INCI name % w/w CAS"]
    # няма правдоподобна двойка име+стойност -> празно (заглавен ред)
    out = parse_composition(lines)
    assert out == []


def test_composition_legend_codes_in_region():
    # ARDA-стил: секция с легенда-кодове A–G → диапазони/остатък.
    lines = [
        "COMPOSIZIONE INCI / INCI COMPOSITION:",
        "Propylene Glycol A",
        "Aqua C",
        "Rosmarinus officinalis Leaf Extract C",
        "LEGENDA / INDEX:",
        "A Superiore al 50 % - Above 50 %",
        "C Compreso tra 10 % e 24,9 %",
    ]
    out = parse_composition(lines)
    assert {"inci_name": "Propylene Glycol", "remainder": True} in out
    assert {"inci_name": "Aqua", "range": [10.0, 24.9]} in out
    # легенда-дефиниращите редове не стават съставки
    assert all("Above" not in c["inci_name"] for c in out)


def test_region_focus_ignores_specs_outside_section():
    lines = [
        "Sede legale: via Romagna, 13",
        "pH (sol 10%) 4,5 - 6,5",
        "COMPOSIZIONE INCI / INCI COMPOSITION:",
        "Aqua C",
        "LEGENDA / INDEX:",
    ]
    out = parse_composition(lines)
    assert out == [{"inci_name": "Aqua", "range": [10.0, 24.9]}]


# ---------- ароматни алергени (IFF / Symrise) ----------

def test_fragrance_name_first_iff():
    lines = ["Anethole 104-46-1/ 4180-23-8 0.002"]
    out = parse_fragrance(lines)
    assert out == [{"name": "Anethole", "cas": "104-46-1", "pct_in_fragrance": 0.002}]


def test_fragrance_cas_first_symrise_with_annex():
    lines = ["2050-08-0 Amyl Salicylate III / 328 1,452"]
    out = parse_fragrance(lines)
    assert out == [{"name": "Amyl Salicylate", "cas": "2050-08-0", "pct_in_fragrance": 1.452}]


def test_fragrance_skips_nd():
    lines = ["92-48-8 6-Methyl Coumarin III / 46 n.d."]
    assert parse_fragrance(lines) == []


def test_fragrance_skips_dashes():
    lines = ["32388-55-9 Acetyl Cedrene ----"]
    assert parse_fragrance(lines) == []


def test_fragrance_skips_header_without_cas():
    lines = ["Holzminden, 18-Aug-2025 Page 2 of 5"]
    assert parse_fragrance(lines) == []


def test_looks_like_fragrance_by_keyword():
    assert looks_like_fragrance(["EU Extended Fragrance allergens"], "x.pdf") is True
    assert looks_like_fragrance(["Technical specification rosemary"], "x.pdf") is False


# ---------- draft / YAML ----------

def test_draft_fragment_is_valid_yaml_and_loads_back():
    import yaml
    rm = raw_material_draft("Oleophen", 3.0,
                            constituents=[{"inci_name": "Helianthus Annuus Seed Oil",
                                           "range": [45.0, 55.0]}])
    text = to_yaml([rm])
    doc = yaml.safe_load(text)
    assert doc["raw_materials"][0]["name"] == "Oleophen"
    assert doc["raw_materials"][0]["dose_pct"] == 3.0


# ---------- филтър на не-INCI кандидати (в енджина, не в UX) ----------

def test_filter_drops_boilerplate_keeps_real_inci():
    rms = [{
        "name": "Oleophen",
        "dose_pct": 3.0,
        "composition": [
            {"inci_name": "Helianthus Annuus Seed Oil", "range": [45.0, 55.0]},
            {"inci_name": "Registration according to REACh 1907/2006", "pct": 1.0},
        ],
    }]
    out, dropped = filter_candidates(rms)
    assert dropped == 1
    names = [c["inci_name"] for c in out[0]["composition"]]
    assert names == ["Helianthus Annuus Seed Oil"]


def test_filter_keeps_colour_index_and_empty_when_no_drops():
    rms = [{
        "name": "Pigment",
        "dose_pct": 2.0,
        "composition": [{"inci_name": "CI 77491", "pct": 2.0}],
    }]
    out, dropped = filter_candidates(rms)
    assert dropped == 0
    assert out[0]["composition"] == [{"inci_name": "CI 77491", "pct": 2.0}]
