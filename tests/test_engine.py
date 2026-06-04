"""
Тестове, които доказват регулаторната логика.
Пускане: python -m pytest tests/ -v   (или python tests/test_engine.py)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pif_engine.models import (
    Product, ProductType, Ingredient, FormulaLine, Claim, AllergenContent, ToxProfile
)
from pif_engine.allergens import allergens_to_declare, generate_inci, ALLERGEN_THRESHOLD
from pif_engine.claims import validate_claim
from pif_engine.toxicology import calculate_mos


def _fragrance(fraction):
    return Ingredient(
        inci_name="Parfum", cas="-", function="aroma", is_fragrance=True,
        has_sds=True, has_coa=True, has_ifra=True,
        allergens=[AllergenContent("Limonene", "5989-27-5", fraction)],
    )


def test_allergen_threshold_leave_on_vs_rinse_off():
    """Същата формула: leave-on декларира, rinse-off не (различни прагове)."""
    # parfum 0.5% × 0.01 = 0.005% алерген
    # leave-on праг 0.001% -> декларира; rinse-off праг 0.01% -> НЕ
    parfum = _fragrance(0.01)
    aqua = Ingredient("Aqua", "7732-18-5", "solvent", has_sds=True, has_coa=True)

    leave = Product("L", ProductType.LEAVE_ON,
                    [FormulaLine(aqua, 99.5), FormulaLine(parfum, 0.5)])
    rinse = Product("R", ProductType.RINSE_OFF,
                    [FormulaLine(aqua, 99.5), FormulaLine(parfum, 0.5)])

    assert "Limonene" in allergens_to_declare(leave), "leave-on трябва да декларира"
    assert "Limonene" not in allergens_to_declare(rinse), "rinse-off не трябва"
    print("✅ test_allergen_threshold")


def test_inci_descending_with_allergens_after_parfum():
    parfum = _fragrance(0.20)
    aqua = Ingredient("Aqua", "7732-18-5", "solvent", has_sds=True, has_coa=True)
    gly = Ingredient("Glycerin", "56-81-5", "humectant", has_sds=True, has_coa=True)

    p = Product("X", ProductType.LEAVE_ON, [
        FormulaLine(gly, 10.0), FormulaLine(aqua, 89.0), FormulaLine(parfum, 1.0),
    ])
    inci = generate_inci(p)
    assert inci[0] == "Aqua"        # най-висока концентрация първа
    assert inci[1] == "Glycerin"
    assert inci.index("Limonene") > inci.index("Parfum")  # алерген след Parfum
    print("✅ test_inci_order")


def test_denigrating_claim_blocked():
    r = validate_claim(Claim("Без парабени"))
    assert r.status == "blocked"
    print("✅ test_denigrating_blocked")


def test_normal_claim_approved():
    r = validate_claim(Claim("Подходящ за всеки тип кожа"))
    assert r.status == "approved"
    print("✅ test_normal_approved")


def test_mos_unsafe_flagged():
    """Висок приложен товар + нисък PoD + пълна абсорбция -> MoS < 100."""
    risky = Ingredient(
        "RiskyActive", "000-00-0", "active", has_sds=True, has_coa=True,
        tox=ToxProfile(pod=0.5, dermal_absorption=1.0),
    )
    # A = 100 g × 1.0 ретенция × 1000 / 60 = 1666.7 mg/kg bw/day
    # SED = 1666.7 × 0.5 × 1.0 = 833 -> MoS = 0.5/833 << 100
    p = Product("Z", ProductType.LEAVE_ON, [FormulaLine(risky, 50.0)],
                applied_amount_g=100.0, retention_factor=1.0)
    results = calculate_mos(p)
    assert results[0].is_safe is False
    print("✅ test_mos_unsafe")



def test_sulfate_free_blocked():
    """Реален случай от MANE: 'Без сулфати' е денигрираща -> блокира."""
    r = validate_claim(Claim("Без сулфати"))
    assert r.status == "blocked"
    print("✅ test_sulfate_free_blocked")


def test_growth_claim_needs_evidence():
    r = validate_claim(Claim("Стимулира растежа на косата"))
    assert r.status == "needs_evidence"
    print("✅ test_growth_needs_evidence")


if __name__ == "__main__":
    test_allergen_threshold_leave_on_vs_rinse_off()
    test_inci_descending_with_allergens_after_parfum()
    test_denigrating_claim_blocked()
    test_normal_claim_approved()
    test_mos_unsafe_flagged()
    test_sulfate_free_blocked()
    test_growth_claim_needs_evidence()
    print("\n🎉 Всички тестове минаха.")

