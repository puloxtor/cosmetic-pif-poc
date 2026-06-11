"""Пуска SK5071025 — Beard Oil (DEMO) през енджина:
sum-alarm, master композиция, алергени, INCI (Член 19)."""
from data.sk5071025_beard_oil import sk5071025_beard_oil as p
from pif_engine.allergens import (
    calculate_allergens, allergens_to_declare, generate_inci, _consolidated_lines,
)
from pif_engine.allergens import ALLERGEN_THRESHOLD


def main():
    print(f"ПРОДУКТ: {p.name}")
    print(f"Тип: {p.product_type.value}  (праг алерген {ALLERGEN_THRESHOLD[p.product_type]}%)\n")

    total = sum(l.concentration_pct for l in p.formula)
    print("=== ПРОВЕРКА НА СБОРА ===")
    if abs(total - 100.0) > 1e-9:
        print(f"⚠️  Сборът не е 100% — {total:.3f}%\n")
    else:
        print(f"OK — {total:.3f}%\n")

    print("=== MASTER КОМПОЗИЦИЯ (обединена по INCI) ===")
    for l in sorted(_consolidated_lines(p), key=lambda l: l.concentration_pct, reverse=True):
        print(f"  {l.ingredient.inci_name:<32} {l.concentration_pct:8.3f}%   CAS {l.ingredient.cas}")
    print()

    print("=== АЛЕРГЕНИ (принос в продукта) ===")
    totals = calculate_allergens(p)
    thr = ALLERGEN_THRESHOLD[p.product_type]
    declared = set(allergens_to_declare(p))
    for name in sorted(totals, key=lambda n: totals[n], reverse=True):
        flag = "ДЕКЛАРИРА СЕ" if name in declared else "под прага"
        print(f"  {name:<28} {totals[name]:9.5f}%   {flag}")
    print()

    print("=== ФИНАЛЕН INCI (Член 19) ===")
    for i, name in enumerate(generate_inci(p), 1):
        print(f"  {i:>2}. {name}")


if __name__ == "__main__":
    main()
