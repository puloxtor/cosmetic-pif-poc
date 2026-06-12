"""R8: всяко 'fixed' findings в validation/log.yaml трябва да има regression_guard,
сочещ към СЪЩЕСТВУВАЩ тестов файл — затваря цикъла fix → регресионен тест.

Така повторение на Finding C (поправено, но без защита срещу регрес) не може да мине.
"""
from __future__ import annotations
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "validation" / "log.yaml"


def _fixed_findings():
    data = yaml.safe_load(LOG.read_text(encoding="utf-8"))
    for entry in data:
        for f in entry.get("findings", []):
            if f.get("status") == "fixed":
                yield entry.get("product_id", "?"), f


def test_fixed_findings_have_regression_guard():
    missing = [f"{pid}/{f.get('id')}" for pid, f in _fixed_findings()
               if not f.get("regression_guard")]
    assert not missing, f"'fixed' findings без regression_guard: {missing}"


def test_regression_guard_paths_exist():
    bad = []
    for pid, f in _fixed_findings():
        guard = f.get("regression_guard")
        if not guard:
            continue
        test_file = guard.split("::", 1)[0]
        if not (ROOT / test_file).exists():
            bad.append(f"{pid}/{f.get('id')}: {test_file}")
    assert not bad, f"regression_guard сочи липсващ файл: {bad}"
