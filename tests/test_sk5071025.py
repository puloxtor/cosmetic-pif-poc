"""Регресионни тестове за SK5071025 — Beard Oil (DEMO).
Заключва очакваните стойности от енджин-пайплайна (sum-alarm, master
композиция, алергени, INCI ред — алергените трасират пълния списък)."""
from data.sk5071025_beard_oil import sk5071025_beard_oil as p
from pif_engine.allergens import (
    calculate_allergens, allergens_to_declare, generate_inci, _consolidated_lines,
)


def test_sum_exceeds_100():
    total = sum(l.concentration_pct for l in p.formula)
    assert abs(total - 103.54) < 1e-6   # worst-case Oleophen инфлация


def test_master_composition_consolidated():
    comp = {l.ingredient.inci_name: round(l.concentration_pct, 3)
            for l in _consolidated_lines(p)}
    assert comp["Prunus Amygdalus Dulcis Oil"] == 69.5
    assert comp["Ricinus Communis Seed Oil"] == 20.0
    # Oleophen worst-case горни граници
    assert comp["Olea Europaea Fruit Oil"] == 1.05
    assert comp["Cucurbita Pepo Seed Oil"] == 0.6
    assert comp["Hippophae Rhamnoides Oil"] == 0.24
    # Sunflower-носителят на Vitapherole се обединява с Helianthus по INCI
    assert comp["Helianthus Annuus Seed Oil"] == 1.8
    assert comp["Tocopherol"] == 0.35


def test_declared_allergens_leave_on():
    declared = set(allergens_to_declare(p))
    # над прага 0.001%
    for a in ["Limonene", "Linalool", "Citral", "Coumarin",
              "Citrus Aurantium Peel Oil", "Hexamethylindanopyran",
              "Amyl Salicylate", "Beta-Caryophyllene", "Lavandula Oil Extract",
              "Linalyl Acetate", "Eugenol", "Geranyl Acetate"]:
        assert a in declared
    # под прага
    for a in ["Eucalyptus Globulus Oil", "Alpha-Terpinene",
              "3-Propylidenephthalide", "Citronellol", "Geraniol", "Isoeugenol"]:
        assert a not in declared
    assert len(declared) == 12


def test_allergen_concentrations():
    t = calculate_allergens(p)
    assert round(t["Limonene"], 5) == 0.12
    assert round(t["Citral"], 5) == 0.00639
    assert round(t["Beta-Caryophyllene"], 5) == 0.00486


def test_allergens_trail_full_ingredient_list():
    inci = generate_inci(p)
    ingredient_names = [l.ingredient.inci_name for l in _consolidated_lines(p)]
    declared = allergens_to_declare(p)
    # последният не-алерген индекс е преди първия алерген индекс
    last_ingredient = max(inci.index(n) for n in ingredient_names)
    first_allergen = min(inci.index(a) for a in declared)
    assert last_ingredient < first_allergen
    # Parfum е част от съставките, не последен
    assert inci.index("Parfum") < first_allergen
    # алергените са в самия край
    assert inci[-len(declared):] == declared
