"""Тестове за картата правило → правно основание (Finding R4)."""
from __future__ import annotations
from pif_engine import REGULATORY_REFS


def test_refs_nonempty_strings():
    assert REGULATORY_REFS
    assert all(isinstance(k, str) and isinstance(v, str) and v
               for k, v in REGULATORY_REFS.items())


def test_core_rules_cite_sources():
    assert "1223/2009" in REGULATORY_REFS["ALLERGEN_THRESHOLD"]
    assert "1223/2009" in REGULATORY_REFS["ART_19_INCI"]
    assert "MoS" in REGULATORY_REFS["MOS_SAFETY_THRESHOLD"]
