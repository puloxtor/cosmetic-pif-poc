"""Тестове за типизираната йерархия от грешки (Finding R2)."""
from __future__ import annotations
import pytest
from pif_engine import build_product, PifError, PifInputError, PifDataGapError


def _doc(raw_materials, product=None):
    return {"product": product or {"name": "x", "product_type": "leave-on"},
            "raw_materials": raw_materials}


def test_missing_product_section_is_input_error():
    with pytest.raises(PifInputError):
        build_product({"raw_materials": []})


def test_missing_product_type_is_input_error():
    with pytest.raises(PifInputError):
        build_product({"product": {"name": "x"}, "raw_materials": [
            {"name": "a", "dose_pct": 1.0,
             "composition": [{"inci_name": "X", "pct": 100}]}]})


def test_missing_raw_materials_is_input_error():
    with pytest.raises(PifInputError):
        build_product({"product": {"name": "x", "product_type": "leave-on"}})


def test_missing_dose_is_datagap():
    with pytest.raises(PifDataGapError):
        build_product(_doc([{"name": "a",
                             "composition": [{"inci_name": "X", "pct": 100}]}]))


def test_missing_composition_is_datagap():
    with pytest.raises(PifDataGapError):
        build_product(_doc([{"name": "a", "dose_pct": 100.0}]))


def test_hierarchy_and_valueerror_compat():
    # Всичко наследява PifError…
    assert issubclass(PifInputError, PifError)
    assert issubclass(PifDataGapError, PifError)
    # …и ValueError, за да продължи да работи старият `except ValueError`.
    assert issubclass(PifInputError, ValueError)
    assert issubclass(PifDataGapError, ValueError)
