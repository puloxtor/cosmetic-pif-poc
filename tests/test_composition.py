"""
Тестове за композиционния компилатор и YAML зареждането.
Пускай: python3 -m pytest tests/ -v
"""
import os

from pif_engine.composition import (
    resolve_amount, build_product, consolidated_concentrations, SUM_TOLERANCE,
)
from pif_engine.loader import load_product
from pif_engine.allergens import generate_inci, allergens_to_declare

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "beard_oil_sk5071025.yaml")


# ---------- resolve_amount: единични случаи ----------

def test_resolve_exact():
    upper, lower, note, is_rem = resolve_amount({"pct": 42})
    assert upper == 42 and lower == 42 and is_rem is False


def test_resolve_range_takes_upper():
    upper, lower, note, is_rem = resolve_amount({"range": [10, 24.9]})
    assert upper == 24.9 and lower == 10 and is_rem is False


def test_resolve_at_most():
    upper, lower, note, is_rem = resolve_amount({"at_most": 1.0})
    assert upper == 1.0 and lower == 0.0


def test_resolve_remainder_flagged():
    upper, lower, note, is_rem = resolve_amount({"remainder": True})
    assert is_rem is True


def test_remainder_computed_from_others_lower_bounds():
    # Propylene Glycol "над 50%" като остатък след минимумите на другите.
    doc = {
        "product": {"name": "t", "product_type": "leave-on"},
        "raw_materials": [{
            "name": "Glycolic Extract", "dose_pct": 100.0,
            "composition": [
                {"inci_name": "Propylene Glycol", "remainder": True},
                {"inci_name": "Aqua", "range": [10, 24.9]},
                {"inci_name": "Rosmarinus Officinalis Leaf Extract", "range": [10, 24.9]},
            ],
        }],
    }
    product, _ = build_product(doc)
    conc = consolidated_concentrations(product)
    # остатък = 100 - (10 + 10) = 80 (долни граници на другите)
    assert abs(conc["Propylene Glycol"] - 80.0) < 1e-6
    assert abs(conc["Aqua"] - 24.9) < 1e-6


# ---------- Реалният фикстур (Beard oil) ----------

def test_fixture_loads():
    product, warnings = load_product(FIXTURE)
    assert product.formula, "формулата не трябва да е празна"


def test_sum_alarm_fires_on_103_percent():
    _, warnings = load_product(FIXTURE)
    assert any("≠ 100%" in w for w in warnings), warnings


def test_duplicate_inci_are_summed():
    product, _ = load_product(FIXTURE)
    conc = consolidated_concentrations(product)
    # Helianthus: Oleophen 3×0.55 + Vitapherole 0.5×0.30 = 1.65 + 0.15 = 1.80
    assert abs(conc["Helianthus Annuus Seed Oil"] - 1.80) < 1e-6
    # Tocopherol: Oleophen 3×0.009 + Vitapherole 0.5×0.70 = 0.027 + 0.35 = 0.377
    assert abs(conc["Tocopherol"] - 0.377) < 1e-6


def test_range_upper_bound_applied():
    product, _ = load_product(FIXTURE)
    conc = consolidated_concentrations(product)
    # Olea: 3 × 35/100 = 1.05 (горна граница на 25-35)
    assert abs(conc["Olea Europaea Fruit Oil"] - 1.05) < 1e-6
    # Hippophae: 3 × 8/100 = 0.24
    assert abs(conc["Hippophae Rhamnoides Oil"] - 0.24) < 1e-6


def test_parfum_allergen_concentration():
    product, _ = load_product(FIXTURE)
    # Limonene: парфюм 3% × 4.000% = 0.12% в продукта
    from pif_engine.allergens import calculate_allergens
    totals = calculate_allergens(product)
    assert abs(totals["Limonene"] - 0.12) < 1e-9


def test_inci_order_and_allergens_after_parfum():
    product, _ = load_product(FIXTURE)
    inci = generate_inci(product)
    assert inci[0] == "Prunus Amygdalus Dulcis Oil"
    assert inci[1] == "Ricinus Communis Seed Oil"
    assert "Parfum" in inci
    assert "Limonene" in inci
    # алергените се появяват СЛЕД Parfum
    assert inci.index("Limonene") > inci.index("Parfum")


def test_leave_on_allergen_threshold_declares_limonene():
    product, _ = load_product(FIXTURE)
    declared = allergens_to_declare(product)
    assert "Limonene" in declared           # 0.12% > 0.001% (leave-on)
    assert "Geraniol" not in declared        # 0.00006% < праг
