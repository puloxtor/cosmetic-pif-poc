"""Тестове за структурираните предупреждения (Finding R5).

EngineWarning трябва да е напълно съвместим назад (подклас на str) и да носи
машинно-четими severity/code/subject, които управляват гейта в UX-а (R6).
"""
from __future__ import annotations
from pif_engine import build_product, EngineWarning, Severity


def _warns(doc):
    _, warnings = build_product(doc)
    return warnings


def _by_code(warnings, code):
    return [w for w in warnings if isinstance(w, EngineWarning) and w.code == code]


def test_engine_warning_is_str_subclass():
    w = EngineWarning(Severity.WARNING, "X", "⚠️ нещо", subject="s")
    assert isinstance(w, str)
    assert str(w) == "⚠️ нещо"
    assert "нещо" in w                      # __contains__ от str
    assert w.lower() == "⚠️ нещо".lower()
    assert w.message == "⚠️ нещо"
    assert (w.severity, w.code, w.subject) == (Severity.WARNING, "X", "s")


def test_sum_not_100_is_warning():
    doc = {
        "product": {"name": "T", "product_type": "leave-on"},
        "raw_materials": [
            {"name": "Oil", "dose_pct": 90.0,
             "composition": [{"inci_name": "Prunus Amygdalus Dulcis Oil", "pct": 100}]},
        ],
    }
    ws = _by_code(_warns(doc), "SUM_NOT_100")
    assert len(ws) == 1 and ws[0].severity == Severity.WARNING
    assert "≠ 100%" in ws[0]


def test_range_note_is_info():
    doc = {
        "product": {"name": "T", "product_type": "leave-on"},
        "raw_materials": [
            {"name": "Mix", "dose_pct": 100.0, "composition": [
                {"inci_name": "Helianthus Annuus Seed Oil", "range": [45, 55]},
                {"inci_name": "Prunus Amygdalus Dulcis Oil", "pct": 45},
            ]},
        ],
    }
    ws = _by_code(_warns(doc), "RESOLVE_RULE_NOTE")
    assert ws and all(w.severity == Severity.INFO for w in ws)
    assert all(w.startswith("ℹ️") for w in ws)


def test_remainder_is_warning():
    doc = {
        "product": {"name": "T", "product_type": "leave-on"},
        "raw_materials": [
            {"name": "Ext", "dose_pct": 100.0, "composition": [
                {"inci_name": "Propylene Glycol", "remainder": True},
                {"inci_name": "Aqua", "range": [10, 24.9]},
            ]},
        ],
    }
    ws = _by_code(_warns(doc), "REMAINDER_ACCEPTED")
    assert ws and ws[0].severity == Severity.WARNING


def test_unknown_fragrance_allergen_is_warning():
    doc = {
        "product": {"name": "T", "product_type": "leave-on"},
        "raw_materials": [
            {"name": "Parfum", "dose_pct": 100.0, "is_fragrance": True,
             "allergens": [{"name": "Totally Fake Allergen ZZZ", "pct_in_fragrance": 5.0}]},
        ],
    }
    ws = _by_code(_warns(doc), "FRAGRANCE_UNKNOWN_ALLERGEN")
    assert ws and ws[0].severity == Severity.WARNING and ws[0].subject == "Parfum"


def test_every_warning_has_valid_severity():
    doc = {
        "product": {"name": "T", "product_type": "leave-on"},
        "raw_materials": [
            {"name": "Mix", "dose_pct": 90.0, "composition": [
                {"inci_name": "Helianthus Annuus Seed Oil", "range": [45, 55]},
            ]},
        ],
    }
    for w in _warns(doc):
        assert isinstance(w, EngineWarning)
        assert w.severity in Severity.ALL and w.code
