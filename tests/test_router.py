"""
Тестове за маршрутизатора на извличането (без мрежа/реални файлове).
AI-зрението се мокква; тестваме само решенията за маршрут и сглобяването.
"""
import pif_engine.extraction.router as router
from pif_engine.extraction import vision


def test_extension_helpers():
    assert router._is_pdf("a.PDF")
    assert not router._is_pdf("a.png")
    assert router._is_image("b.JPG")
    assert not router._is_image("c.pdf")


def test_force_vision_composition(monkeypatch):
    monkeypatch.setattr(vision, "extract",
                        lambda p, k, m=None: ([{"inci_name": "Aqua", "pct": 100}], ["n"]))
    rms, notes = router.extract_drafts("x.pdf", kind="composition", ocr_mode="force",
                                       name="X", dose=10)
    assert len(rms) == 1
    assert rms[0]["name"] == "X" and rms[0]["dose_pct"] == 10
    assert rms[0]["composition"] == [{"inci_name": "Aqua", "pct": 100}]
    assert any("AI-зрение" in n for n in notes)


def test_force_vision_formula_returns_many(monkeypatch):
    monkeypatch.setattr(vision, "extract", lambda p, k, m=None: (
        [{"name": "Almond", "dose_pct": 69.5, "composition": []},
         {"name": "Parfum", "dose_pct": 3.0, "composition": []}], []))
    rms, _ = router.extract_drafts("recipe.jpg", kind="formula", ocr_mode="force")
    assert [r["name"] for r in rms] == ["Almond", "Parfum"]


def test_force_vision_fragrance(monkeypatch):
    monkeypatch.setattr(vision, "extract", lambda p, k, m=None: (
        [{"name": "Limonene", "cas": "138-86-3", "pct_in_fragrance": 4.0}], []))
    rms, _ = router.extract_drafts("p.pdf", kind="fragrance", ocr_mode="force", dose=1.0)
    assert rms[0]["is_fragrance"] is True
    assert rms[0]["allergens"][0]["name"] == "Limonene"


def test_never_ocr_image_returns_empty_draft():
    rms, notes = router.extract_drafts("photo.png", ocr_mode="never", name="P", dose=5)
    assert rms[0]["composition"] == []
    assert any("OCR е забранен" in n for n in notes)
