"""
Тестове за денатурантния филтър (Член 19) и одитната следа в CPSR.

Денатурантът присъства в суровината (документира се в Част А), но НЕ влиза в
етикетната INCI листа според функцията си. Не е тих пропуск — CPSR Част А
изброява явно всяка изключена съставка. Един източник (suppressed_ingredients)
управлява И филтъра в generate_inci, И одитната бележка (CLAUDE.md).
"""
from pif_engine.composition import build_product, suppressed_ingredients
from pif_engine.allergens import generate_inci
from pif_engine.cpsr import generate_cpsr


def _doc():
    """Продукт с алкохолна суровина, носеща денатурант SD Alcohol 40-B."""
    return {
        "product": {"name": "Test Tonic", "product_type": "leave-on"},
        "raw_materials": [
            {
                "name": "Aqua",
                "dose_pct": 60.0,
                "composition": [{"inci_name": "Aqua", "pct": 100.0}],
            },
            {
                "name": "Denatured Alcohol",
                "dose_pct": 40.0,
                "composition": [
                    {"inci_name": "Alcohol", "pct": 99.0,
                     "function": "solvent"},
                    {"inci_name": "SD Alcohol 40-B", "pct": 1.0,
                     "function": "denaturant"},
                ],
            },
        ],
    }


def test_denaturant_absent_from_inci():
    product, _ = build_product(_doc())
    inci = generate_inci(product)
    assert "SD Alcohol 40-B" not in inci
    # реалните съставки остават
    assert "Aqua" in inci
    assert "Alcohol" in inci


def test_denaturant_present_in_suppressed():
    product, _ = build_product(_doc())
    suppressed = suppressed_ingredients(product)
    names = [ing.inci_name for ing in suppressed]
    assert names == ["SD Alcohol 40-B"]


def test_cpsr_audit_note_lists_denaturant():
    product, _ = build_product(_doc())
    report = generate_cpsr(product)
    # денатурантът остава ВИДИМ в пълната таблица на Част А (A.1)
    assert "SD Alcohol 40-B" in report
    # ... и има ясна одитна бележка ЗАЩО е изключен от INCI
    assert "Изключено от INCI декларацията" in report
    assert "не се декларира" in report
    # бележката споменава конкретната съставка
    assert report.count("SD Alcohol 40-B") >= 2
