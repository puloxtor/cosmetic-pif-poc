"""Тестове за произхода в CPSR долния колонтитул (Finding R3)."""
from __future__ import annotations
import pathlib
import yaml

import pif_engine.provenance as P
from pif_engine import build_product, generate_cpsr, engine_provenance, __version__
from pif_engine.allergens import ALLERGEN_THRESHOLD
from pif_engine.toxicology import MOS_SAFETY_THRESHOLD

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "beard_oil_sk5071025.yaml"


def _product():
    doc = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    p, _ = build_product(doc)
    return p


def test_footer_has_version_and_thresholds():
    p = _product()
    report = generate_cpsr(p)
    assert "Произход на доклада" in report
    assert __version__ in report
    assert str(MOS_SAFETY_THRESHOLD) in report
    assert str(ALLERGEN_THRESHOLD[p.product_type]) in report


def test_provenance_keys_and_version():
    prov = engine_provenance()
    assert set(prov) == {"version", "sha", "source"}
    assert prov["version"] == __version__


def test_provenance_never_raises(monkeypatch):
    monkeypatch.setattr(P, "_sha_from_direct_url", lambda: None)
    monkeypatch.setattr(P, "_sha_from_git", lambda: None)
    prov = P.engine_provenance()
    assert prov["sha"] == "unknown" and prov["source"] == "none"


def test_provenance_reads_direct_url(monkeypatch):
    import importlib.metadata as m

    class FakeDist:
        def read_text(self, name):
            assert name == "direct_url.json"
            return ('{"url":"git+https://x",'
                    '"vcs_info":{"vcs":"git","commit_id":"abcdef1234567890deadbeef"}}')

    monkeypatch.setattr(m, "distribution", lambda name: FakeDist())
    prov = P.engine_provenance()
    assert prov["source"] == "direct_url"
    assert prov["sha"] == "abcdef123456"   # скъсено до 12 знака
