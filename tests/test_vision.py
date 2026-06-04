"""
Тестове за ДЕТЕРМИНИСТИЧНИТЕ помощници на AI-зрението (без мрежа/API).
Тестваме преобразуването на суровия текст от модела към spec — точно там,
където числата стават структура (а не самото OCR четене).
"""
import pytest

from pif_engine.extraction import vision


# ---- amount_to_spec ----

def test_amount_exact():
    assert vision.amount_to_spec("100") == {"pct": 100.0}
    assert vision.amount_to_spec("0,9 %") == {"pct": 0.9}


def test_amount_range():
    assert vision.amount_to_spec("45-55") == {"range": [45.0, 55.0]}
    assert vision.amount_to_spec("10 – 24,9 %") == {"range": [10.0, 24.9]}


def test_amount_above_is_remainder():
    assert vision.amount_to_spec("above 50%") == {"remainder": True}
    assert vision.amount_to_spec("над 50 %") == {"remainder": True}


def test_amount_at_most():
    assert vision.amount_to_spec("<= 1") == {"at_most": 1.0}
    assert vision.amount_to_spec("до 0,5%") == {"at_most": 0.5}


def test_amount_unknown():
    assert vision.amount_to_spec("") is None
    assert vision.amount_to_spec("qs") is None


# ---- мапери модел-JSON → чернова ----

def test_to_composition_maps_and_flags():
    data = {
        "constituents": [
            {"inci_name": "Helianthus Annuus Seed Oil", "cas": "8001-21-6", "amount": "45-55"},
            {"inci_name": "Tocopherol", "cas": "59-02-9", "amount": "0,9"},
            {"inci_name": "Mystery", "cas": "", "amount": "qs"},
        ],
        "notes": [],
    }
    out, notes = vision.to_composition(data)
    assert {"inci_name": "Helianthus Annuus Seed Oil", "cas": "8001-21-6", "range": [45.0, 55.0]} in out
    assert {"inci_name": "Tocopherol", "cas": "59-02-9", "pct": 0.9} in out
    # нечетимото количество не получава стойност, но се отбелязва
    assert any("Mystery" in n for n in notes)


def test_to_fragrance_skips_unreadable():
    data = {
        "allergens": [
            {"name": "Limonene", "cas": "138-86-3", "pct_in_fragrance": "4.0"},
            {"name": "Bad", "cas": "", "pct_in_fragrance": ""},
        ],
        "notes": [],
    }
    out, notes = vision.to_fragrance(data)
    assert out == [{"name": "Limonene", "cas": "138-86-3", "pct_in_fragrance": 4.0}]
    assert any("Bad" in n for n in notes)


def test_to_formula():
    data = {"product_name": "Beard oil", "raw_materials": [
        {"name": "Sweet Almond Oil", "dose_pct": "69,5"},
        {"name": "Parfum", "dose_pct": "3"},
    ], "notes": []}
    out, _ = vision.to_formula(data)
    assert out[0] == {"name": "Sweet Almond Oil", "dose_pct": 69.5, "composition": []}
    assert out[1]["dose_pct"] == 3.0


# ---- media type ----

def test_detect_media_type():
    assert vision.detect_media_type("a.pdf") == "application/pdf"
    assert vision.detect_media_type("b.JPG") == "image/jpeg"
    assert vision.detect_media_type("c.png") == "image/png"
    with pytest.raises(ValueError):
        vision.detect_media_type("d.txt")
